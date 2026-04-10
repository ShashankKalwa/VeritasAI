"""
VeritasAI ML Model — TF-IDF + Logistic Regression Classifier
Trained on the 500-row labeled dataset from Supabase.
Combines with heuristic engine for ensemble predictions.
"""
import logging
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

logger = logging.getLogger(__name__)


class FakeNewsClassifier:
    """
    TF-IDF + Logistic Regression fake news classifier.
    Trained on labeled headlines dataset from Supabase.
    """

    def __init__(self):
        self.pipeline: Pipeline | None = None
        self.is_trained = False

    def train(self, headlines: list[str], labels: list[str]):
        """Train the model on labeled data."""
        if len(headlines) < 10:
            logger.warning("Not enough training data, need at least 10 samples")
            return False

        try:
            self.pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(
                    max_features=5000,
                    ngram_range=(1, 3),
                    stop_words="english",
                    min_df=1,
                    max_df=0.95,
                    sublinear_tf=True,
                )),
                ("clf", LogisticRegression(
                    max_iter=1000,
                    C=1.0,
                    class_weight="balanced",
                    solver="lbfgs",
                )),
            ])

            # Convert labels: fake=1, real=0
            y = np.array([1 if l == "fake" else 0 for l in labels])
            self.pipeline.fit(headlines, y)
            self.is_trained = True

            # Log training accuracy
            train_acc = self.pipeline.score(headlines, y)
            logger.info(f"ML model trained on {len(headlines)} samples, train accuracy: {train_acc:.3f}")
            return True

        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False

    def predict(self, text: str) -> dict | None:
        """Predict fake/real with confidence."""
        if not self.is_trained or not self.pipeline:
            return None

        try:
            proba = self.pipeline.predict_proba([text])[0]
            # proba[0] = real prob, proba[1] = fake prob
            fake_prob = proba[1]
            real_prob = proba[0]

            if fake_prob > real_prob:
                verdict = "FAKE"
                confidence = min(round(fake_prob * 100), 99)
            else:
                verdict = "REAL"
                confidence = min(round(real_prob * 100), 99)

            return {
                "verdict": verdict,
                "confidence": confidence,
                "ml_fake_prob": round(float(fake_prob), 4),
                "ml_real_prob": round(float(real_prob), 4),
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None


# Global singleton
classifier = FakeNewsClassifier()


def get_classifier() -> FakeNewsClassifier:
    return classifier
