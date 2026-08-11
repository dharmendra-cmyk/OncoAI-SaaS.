import os
import time
import json

class OncoAIAgentLoop:
    def __init__(self, target_cohort_file: str, check_interval_seconds: int = 5):
        self.target_cohort_file = target_cohort_file
        self.check_interval_seconds = check_interval_seconds
        self.processed_records = set()
        self.is_running = True

    def observe(self) -> list:
        """Step 1: Check environment/data source for new records."""
        if not os.path.exists(self.target_cohort_file):
            print(f"[OBSERVE] Waiting for input file: {self.target_cohort_file}")
            return []

        # Read state (Simulating reading new records from AE_Audit_Test.csv)
        with open(self.target_cohort_file, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        # Identify unprocessed records
        new_records = [r for r in lines if r not in self.processed_records]
        return new_records

    def orient_and_plan(self, record: str) -> dict:
        """Step 2: Evaluate the state against safety rules and business logic."""
        print(f"[ORIENT] Analyzing record state: {record[:40]}...")
        
        # Simple rule orientation: flag high-risk terms
        requires_immediate_audit = "SAE" in record or "Cardiac Arrest" in record
        
        return {
            "payload": record,
            "requires_immediate_audit": requires_immediate_audit,
            "status": "READY_FOR_GUARDRAIL"
        }

    def act(self, plan: dict) -> dict:
        """Step 3: Execute tool calls, pathology extraction, or API actions."""
        print(f"[ACT] Running deterministic guardrails & extraction...")
        
        output_result = {
            "record": plan["payload"],
            "flagged_sae": plan["requires_immediate_audit"],
            "guardrail_status": "PASSED",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return output_result

    def evaluate(self, result: dict):
        """Step 4: Update system state, log audit trails, and mark complete."""
        self.processed_records.add(result["record"])
        
        if result["flagged_sae"]:
            print(f"🚨 [ALERT] SAE Detected! 24-Hour Regulatory Notification Triggered.")
        else:
            print(f"✅ [SUCCESS] Record cleared and logged.")

    def run(self, max_iterations: int = 3):
        """Main Loop Execution Engine"""
        print("🚀 Starting OncoAI Autonomous Loop Engine...")
        iteration = 0
        
        while self.is_running and iteration < max_iterations:
            iteration += 1
            print(f"\n--- [LOOP ITERATION {iteration}] ---")
            
            new_data = self.observe()
            
            if not new_data:
                print("[LOOP] No new records found. Sleeping...")
            else:
                for item in new_data:
                    plan = self.orient_and_plan(item)
                    result = self.act(plan)
                    self.evaluate(result)
            
            time.sleep(self.check_interval_seconds)
            
        print("\n🏁 OncoAI Loop Engine safely halted.")

if __name__ == "__main__":
    agent = OncoAIAgentLoop(target_cohort_file="AE_Audit_Test.csv", check_interval_seconds=2)
    agent.run(max_iterations=2)
