"""
Test script for prediction agent with simulated data
"""

import sys
sys.path.insert(0, '.')

from agents.prediction_agent import PredictionAgent

print("="*60)
print("  Testing Prediction Agent")
print("="*60)

agent = PredictionAgent()

# Get status
print("\n📊 Current Status:")
status = agent.get_model_status()
print(f"  Database records: {status['database_records']}")
print(f"  Can train: {status['can_train']}")
print(f"  Progress: {status['progress']}")
print(f"  Min required: {status['min_required']}")
print(f"  Ideal samples: {status['ideal_samples']}")

# Try to train
print("\n🎓 Attempting to train model...")
train_result = agent.train_model(force=True)
print(f"  Result: {train_result['message']}")

if train_result.get('success'):
    print(f"  Accuracy: {train_result['accuracy']:.1%}")
    
    # Try prediction
    print("\n🎯 Making prediction...")
    pred = agent.predict_next_day()
    
    if pred['success']:
        print(f"  Prediction: {pred['prediction']}")
        print(f"  Confidence: {pred['confidence']:.1%}")
        print(f"  Up probability: {pred['probability_up']:.1%}")
        print(f"  Down probability: {pred['probability_down']:.1%}")
    else:
        print(f"  Cannot predict: {pred['message']}")
else:
    print("\n⚠️  Cannot train yet - need more data!")
    print(f"   Collect data for {status['min_required'] - status['database_records']} more days")

print("\n" + "="*60)
