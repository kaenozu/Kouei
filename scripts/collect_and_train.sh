#!/bin/bash
# Kouei Data Collection and Model Training Script
set -e

cd /home/exedev/Kouei
source .venv/bin/activate

echo "========================================"
echo "🚀 Kouei Data Collection & Training"
echo "========================================"

# 1. Collect recent data
echo ""
echo "📥 Step 1: Collecting recent race data..."
python3 << 'PYTHON'
import sys
sys.path.insert(0, '/home/exedev/Kouei')
from datetime import datetime, timedelta
from src.collector.collect_data import RaceCollector

collector = RaceCollector()

# Collect last 7 days of data
end_date = datetime.now() - timedelta(days=1)
start_date = end_date - timedelta(days=7)

print(f"Collecting data from {start_date.date()} to {end_date.date()}...")
collector.collect(start_date.date(), end_date.date())
print("✅ Data collection complete!")
PYTHON

# 2. Rebuild dataset
echo ""
echo "🔄 Step 2: Rebuilding dataset..."
python3 << 'PYTHON'
import sys
sys.path.insert(0, '/home/exedev/Kouei')
from src.features.build_dataset_incremental import build_dataset_incremental
build_dataset_incremental()
print("✅ Dataset rebuilt!")
PYTHON

# 3. Train model (optional - controlled by argument)
if [ "$1" == "--train" ]; then
    echo ""
    echo "🧠 Step 3: Training model V3..."
    python3 -c "
import sys
sys.path.insert(0, '/home/exedev/Kouei')
from src.model.train_v3 import train_ensemble_v3
train_ensemble_v3()
"
    echo "✅ Model training complete!"
fi

# 4. Restart services
echo ""
echo "🔄 Step 4: Restarting services..."
sudo systemctl restart kouei-api
sleep 3
echo "✅ Services restarted!"

echo ""
echo "========================================"
echo "✅ All tasks completed successfully!"
echo "========================================"
