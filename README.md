# NVIDIA Informational Gravity Engine

**A Digital Simulation of Tail and Head Theory for Financial Market Prediction**

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

---

## 🌌 Project Vision

The **NVIDIA Informational Gravity Engine** is not merely a stock prediction system—it is a revolutionary digital simulation of **Informational Gravity Theory** applied to financial markets. This system treats financial news as gravitational objects with **mass**, **temporal decay**, and **directional force**, creating a physics-based framework for understanding how information bends price trajectories in spacetime.

At its core, this engine simulates the **Tail and Head Theory** (نظرية الذيل والرأس), where market predictions emerge from the gravitational interaction between news events and their cumulative effect on price probability fields.

---

## 🔬 The Theory: Tail and Head (الذيل والرأس)

### Core Concepts

**The Head (الرأس)** represents the **point of realization**—the expected closing price where informational mass concentrates. This is the focal point where all gravitational forces converge, creating maximum probability density.

**The Tail (الذيل)** represents the **field of probability and uncertainty** derived from conflicting news vectors. When news sources disagree or provide contradictory signals, the tail extends, creating a wide probability distribution that indicates higher risk and lower prediction confidence.

### Physics Framework

#### Informational Gravity
Financial news carries **Informational Mass** ($M_{info}$) that bends the price trajectory through spacetime. Each news article acts as a gravitational body with:

$$M_{info} = f(\text{content\_mass}, \text{source\_credibility}, \text{market\_relevance})$$

Where content mass is derived from financial figures, deals, and quantitative data within the article.

#### Temporal Decay Function
Informational gravity follows a temporal decay model, where news older than 12 hours experiences a 30% force reduction:

$$F_{decay}(t) = \begin{cases} 
1.0 & \text{if } t \leq 12 \text{ hours} \\
0.7 & \text{if } t > 12 \text{ hours}
\end{cases}$$

#### Entropy and Probability Field Width
High entropy occurs when news vectors conflict, creating a **Wide Tail** scenario:

$$\text{Entropy} = H = -\sum_{i} p_i \log_2(p_i)$$

Where $p_i$ represents the probability distribution of sentiment vectors. High entropy ($H > 0.8$) indicates **chaotic information dispersion** and triggers system warnings.

#### Gravity Mass-Weighted Average
The final prediction emerges from the gravitational center of mass:

$$\text{Prediction} = \frac{\sum_{i=1}^{n} M_i \times S_i \times F_{decay}(t_i)}{\sum_{i=1}^{n} M_i \times F_{decay}(t_i)}$$

Where $M_i$ is the informational mass, $S_i$ is the sentiment score, and $F_{decay}(t_i)$ is the temporal decay factor.

---

## ⚙️ Technical Architecture: The Physics Pipeline

### Step 1: Kinetic Data Collection
- **Market Volume & Price Extraction**: Real-time collection of NVIDIA (NVDA) stock data
- **Technical Momentum Indicators**: RSI, MACD, moving averages for **Technical Inertia** calculation
- **Temporal Synchronization**: All data timestamped in New York market timezone

### Step 2: Mass Extraction Engine
- **Deep-Text Scraping**: Full-content extraction using `newspaper3k` and `trafilatura`
- **Financial Mass Detection**: GPT-4o identifies quantitative data (revenue, deals, forecasts)
- **Source Weighting**: Trusted financial sources (Reuters, Bloomberg, WSJ) receive higher gravitational mass
- **Content Physics Analysis**: Each article analyzed as a **Data Physics Object**

### Step 3: Temporal Decay Implementation
- **Age Calculation**: Precise timestamp analysis relative to NY market hours
- **Decay Application**: 30% mass reduction for news > 12 hours old
- **Post-Market Gap Force Detection**: Articles published after 4:00 PM NY flagged for overnight gap potential

### Step 4: Gravity Synthesis & Prediction
- **Batch Processing**: Budget-optimized GPT-4o analysis (83% cost reduction through batching)
- **Physics-Based Prompting**: AI analyzes articles as "informational gravity objects"
- **Range Calculation**: Determines **sentiment_range** (The Tail) and **point_score** (The Head)
- **Entropy Assessment**: Identifies chaos levels in information dispersion

---

## 🚀 Advanced Features

### Dynamic Macro Weighting
When macro-economic news achieves **gravitational mass ≥ 9.0**, the system automatically shifts to a **70% macro / 30% company** weighting scheme. This reflects the reality that high-mass Federal Reserve announcements or GDP data create stronger gravitational fields than individual company news.

```python
if gravitational_mass >= 9.0 and is_macro_event:
    weighting = {"macro": 0.70, "company": 0.30}
    dynamic_weighting_active = True
```

### Entropy-Aware Confidence System
The system continuously monitors **information entropy** and issues warnings during **High Noise** periods:

- **Low Entropy (< 0.4)**: Coherent information alignment → Confidence boost
- **Medium Entropy (0.4-0.7)**: Normal market consensus → Standard confidence  
- **High Entropy (> 0.7)**: Chaotic dispersion → Confidence reduction + Risk warnings

### Gravity Accuracy Calibration
A sophisticated feedback loop compares theoretical predictions against market reality:

- **Physical Match Scoring**: A+ to F grades measuring how well gravity theory predicts actual price movements
- **Continuous Learning**: Model parameters adjust based on **Gravity Accuracy** performance
- **Scientific Validation**: System tracks theoretical coherence vs. empirical results

### Technical Inertia Integration
The system incorporates **Technical Inertia** to prevent unrealistic reversal predictions:

$$\text{Inertia}_{technical} = f(\text{RSI}, \text{moving\_averages}, \text{momentum})$$

High technical inertia requires exceptional **news mass** to overcome established price momentum, preventing the system from predicting trend reversals on weak sentiment signals.

---

## 🗃️ Database Schema

The system utilizes **PostgreSQL** with custom physics-aware columns:

### Daily Data Table
```sql
CREATE TABLE daily_data (
    -- Standard OHLCV data
    date DATE PRIMARY KEY,
    open_price, close_price, high_price, low_price DECIMAL(10,2),
    volume BIGINT,
    
    -- Physics Framework Columns
    sentiment_range TEXT,              -- The Tail: e.g., "-15 to +23"
    entropy VARCHAR(20),               -- Information chaos level
    gravitational_mass NUMERIC(6,2),  -- Combined mass of all news
    gravity_accuracy NUMERIC(6,2),    -- Theoretical vs. actual performance
    
    -- Technical Inertia
    rsi DECIMAL(5,2),
    moving_avg_50 DECIMAL(10,2),
    moving_avg_200 DECIMAL(10,2)
);
```

### Articles Table
```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title TEXT,
    content TEXT,
    source VARCHAR(100),
    published_time TIMESTAMP,
    
    -- Physics Analysis Results
    gravitational_mass NUMERIC(6,2),  -- Individual article mass (0-10)
    sentiment_score DECIMAL(6,2),     -- Field vector (-100 to +100)
    entropy_contribution DECIMAL(4,2), -- Chaos contribution to system
    temporal_decay_factor DECIMAL(3,2) -- Age-based force reduction
);
```

---

## 🛠️ Setup & Execution

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- OpenAI API Key (GPT-4o access)

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/nvidia-gravity-engine.git
cd nvidia-gravity-engine
```

2. **Create virtual environment**:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Database setup**:
```bash
# Create PostgreSQL database
createdb nvidia_gravity

# Run schema migration
python database/setup.py
```

5. **Environment configuration**:
```bash
# Create .env file
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@localhost/nvidia_gravity
```

### Execution

**Full Physics Pipeline**:
```bash
python main.py
```

**Individual Components**:
```bash
# Data collection only
python main.py --collect-data

# Sentiment analysis with temporal physics
python main.py --analyze-sentiment

# Generate predictions with gravity synthesis
python main.py --predict

# Calibrate gravity accuracy
python main.py --calibrate
```

### Monitoring

The system provides real-time physics monitoring:
- **Gravitational Field Visualization**: Range width and entropy levels
- **Technical Inertia Dashboard**: Momentum resistance metrics  
- **Temporal Decay Tracking**: News age and force dissipation
- **Accuracy Calibration Reports**: Theory vs. reality validation

---

## 📊 Physics Validation

The system continuously validates theoretical coherence through:

- **Gravity Accuracy Scores**: Scientific measurement of predictive performance
- **Entropy Pattern Analysis**: Chaos theory validation in market behavior
- **Technical Inertia Validation**: Momentum physics vs. sentiment override events
- **Temporal Decay Verification**: Time-based force dissipation accuracy

---

## 🔬 Research Applications

This **Informational Gravity Engine** serves as a research platform for:

- **Market Physics Theory**: Testing gravitational models in financial systems
- **Information Thermodynamics**: Studying entropy in news flow and market reaction
- **Temporal Force Dynamics**: Understanding how information decays over time
- **Chaos Theory in Finance**: Measuring information dispersion and prediction uncertainty

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

This project welcomes contributions to advance the **Informational Gravity Theory** in financial markets. Please read our [Contributing Guidelines](CONTRIBUTING.md) for physics-based development standards.

---

**"In the quantum realm of financial markets, information is not merely data—it is mass, energy, and gravitational force shaping the spacetime of price discovery."**

*— The Tail and Head Theory*
