"""
Blue-Green Deployment Manager
Manages switching between two model versions (A/B) for zero-downtime updates.
"""
import os
import shutil
import json
from datetime import datetime

MODEL_DIR = "models"
ACTIVE_MODEL_INFO = os.path.join(MODEL_DIR, "active_model.json")

class DeploymentManager:
    def __init__(self, model_dir=MODEL_DIR):
        self.model_dir = model_dir
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

    def _get_active_info(self):
        if not os.path.exists(ACTIVE_MODEL_INFO):
            return {"active": "blue", "path": "models/lgbm_model.txt"}
        with open(ACTIVE_MODEL_INFO, "r") as f:
            return json.load(f)

    def _save_active_info(self, info):
        with open(ACTIVE_MODEL_INFO, "w") as f:
            json.dump(info, f, indent=4)

    def deploy_new_model(self, model_path, version_name=None):
        """
        Deploy a new model to the 'inactive' slot and switch.
        """
        info = self._get_active_info()
        target_slot = "green" if info["active"] == "blue" else "blue"
        target_path = os.path.join(self.model_dir, f"model_{target_slot}.txt")
        
        # Copy new model to target slot
        shutil.copy(model_path, target_path)
        
        # Update info
        new_info = {
            "active": target_slot,
            "path": target_path,
            "version": version_name or datetime.now().strftime("%Y%m%d_%H%M%S"),
            "deployed_at": datetime.now().isoformat()
        }
        self._save_active_info(new_info)
        
        print(f"✅ Deployed to {target_slot} slot: {target_path}")
        return new_info

    def get_current_model_path(self):
        return self._get_active_info()["path"]

# Global instance
deploy_manager = DeploymentManager()

if __name__ == "__main__":
    # Test
    dummy_model = "models/lgbm_model.txt"
    if os.path.exists(dummy_model):
        res = deploy_manager.deploy_new_model(dummy_model, "v2.0-test")
        print(f"Current active: {res['active']} ({res['path']})")
    else:
        print("No base model found to test deployment.")
