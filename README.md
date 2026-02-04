# 🏏 Batsman Bowler Matchup Analysis

A high-performance **Sports Analytics Platform** powered by Machine Learning (XGBoost/RandomForest) to predict the outcome of batsman-bowler face-offs in the Indian Premier League (IPL).


---

## 🚀 Key Features

### 🧠 Matchup Engine
- **Predictive Modelling**: Uses historical ball-by-ball data to predict:
    - **Total Runs**: Expected runs a batsman will score off a specific bowler.
    - **Strike Rate**: Projected aggression level.
    - **Dismissal Chance**: Probability of getting out involved.
    - **Next-Ball Outcome**: Probabilistic breakdown of the very next delivery (Dot, 1, 4, 6, Wicket).

### 🏟️ Venue & Insights
- **Venue Intelligence**: Smart system that adjusts context based on stadium stats (e.g., Wankhede = High Scoring).
- **The Verdict**: Logic-based badge that interprets the stats to declare a winner (e.g., "Bowler Dominates").
- **Visual Analytics**: Interactive gauges and ball-by-ball probability bars.

---

## 🛠️ Tech Stack

- **Backend**: Python (Flask), SQLite
- **ML Core**: XGBoost, Scikit-Learn, Pandas
- **Frontend**: HTML5, Vanilla CSS3 (Variables, Grid, Flexbox), JavaScript (ES6+), Chart.js
- **Design System**: Custom CSS + Bootstrap 5

---

## ⚙️ Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/ipl-matchup-intel.git
    cd ipl-matchup-intel
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Application**
    ```bash
    python app.py
    ```

5.  **Access the App**
    Open your browser and navigate to: `http://127.0.0.1:5000/`

---

## 🧪 Model Details

The system uses a **Voting Ensemble** (XGBoost + Random Forest) for run prediction to balance variance and bias.
- **Dismissal Model**: Calculates the probability of a wicket occurring in the matchup.
- **Ball Classifier**: A specialized XGBoost classifier trained on specific delivery outcomes.

---

## 🤝 Contributing

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

---

