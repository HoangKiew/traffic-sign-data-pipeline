import json
from datetime import datetime
from pathlib import Path
from typing import Tuple

import joblib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import EfficientNetB0, ResNet50
from tensorflow.keras.applications.efficientnet import preprocess_input as eff_preprocess
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess
from tensorflow.keras import layers, models, optimizers


class BaselineTrainer:
    """
    Train baseline:
    - Classical ML (RF / SVM / LogisticRegression) trên features .npy
    - Hoặc CNN end-to-end với transfer learning + augmentation.
    """

    def __init__(
        self,
        model_type: str = "logreg",
        base_model_name: str = "efficientnetb0",
        features_dir: str = "data/features",
        processed_dir: str = "data/processed",
        models_dir: str = "models",
        reports_dir: str = "reports/models",
        seed: int = 42,
        epochs: int = 10,
        batch_size: int = 32,
        fine_tune: bool = False,
    ):
        self.model_type = model_type.lower()
        self.base_model_name = base_model_name.lower()
        self.features_dir = Path(features_dir) / self.base_model_name
        self.processed_dir = Path(processed_dir)
        self.models_dir = Path(models_dir)
        self.reports_dir = Path(reports_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.seed = seed
        self.epochs = epochs
        self.batch_size = batch_size
        self.fine_tune = fine_tune
        self.input_size = (224, 224)

        self.class_indices = self._load_class_indices()
        self.class_names = self._get_class_names()

    # ──────────────── helpers ────────────────
    def _load_class_indices(self):
        path = self.features_dir / "class_indices.json"
        if not path.is_file():
            raise FileNotFoundError(f"Không tìm thấy {path}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _get_class_names(self):
        # class_indices: {class_name: idx}
        inv = {idx: name for name, idx in self.class_indices.items()}
        return [inv[i] for i in range(len(inv))]

    def _load_features_split(self, split: str) -> Tuple[np.ndarray, np.ndarray]:
        x_path = self.features_dir / f"features_{split}.npy"
        y_path = self.features_dir / f"labels_{split}.npy"
        if not x_path.is_file() or not y_path.is_file():
            raise FileNotFoundError(f"Thiếu features hoặc labels cho split '{split}' trong {self.features_dir}")
        X = np.load(x_path)
        y = np.load(y_path)
        return X, y

    # ──────────────── classical ML ────────────────
    def _build_classical_model(self):
        if self.model_type == "logreg":
            # Bỏ multi_class để tránh lỗi version cũ
            clf = LogisticRegression(
                max_iter=1000,
                random_state=self.seed,
                n_jobs=-1,
            )
        elif self.model_type == "svm":
            clf = SVC(kernel="rbf", probability=True, random_state=self.seed)
        elif self.model_type == "rf":
            clf = RandomForestClassifier(
                n_estimators=300, random_state=self.seed, n_jobs=-1
            )
        else:
            raise ValueError("model_type phải là 'logreg', 'svm' hoặc 'rf' (hoặc 'cnn' cho deep model).")

        pipe = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("clf", clf),
            ]
        )
        return pipe

    def _save_confusion_and_per_class_acc(self, y_true, y_pred, suffix: str):
        cm = metrics.confusion_matrix(y_true, y_pred, labels=range(len(self.class_names)))
        acc_per_class = cm.diagonal() / np.maximum(cm.sum(axis=1), 1)

        # Heatmap confusion matrix
        plt.figure(figsize=(6, 5))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=self.class_names,
            yticklabels=self.class_names,
        )
        plt.xlabel("Predicted")
        plt.ylabel("True")
        plt.title(f"Confusion Matrix ({suffix})")
        cm_path = self.reports_dir / f"confusion_matrix_{suffix}.png"
        plt.tight_layout()
        plt.savefig(cm_path, dpi=300)
        plt.close()

        # Per-class accuracy bar chart
        plt.figure(figsize=(6, 4))
        sns.barplot(x=self.class_names, y=acc_per_class)
        plt.ylabel("Accuracy")
        plt.ylim(0, 1.0)
        plt.title(f"Per-class Accuracy ({suffix})")
        plt.xticks(rotation=45, ha="right")
        acc_path = self.reports_dir / f"per_class_accuracy_{suffix}.png"
        plt.tight_layout()
        plt.savefig(acc_path, dpi=300)
        plt.close()

        print(f"  -> Saved confusion matrix: {cm_path}")
        print(f"  -> Saved per-class accuracy: {acc_path}")

    def train_eval_classical(self):
        """
        Train & evaluate classical model trên features .npy.
        """
        print("\n[BaselineTrainer] Load features...")
        X_train, y_train = self._load_features_split("train")
        X_val, y_val = self._load_features_split("val")
        X_test, y_test = self._load_features_split("test")

        print(f"  Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")

        model = self._build_classical_model()
        print(f"\n[BaselineTrainer] Training {self.model_type}...")
        model.fit(X_train, y_train)

        print("\n[BaselineTrainer] Evaluation on test set...")
        y_pred = model.predict(X_test)
        acc = metrics.accuracy_score(y_test, y_pred)
        print(f"  Test accuracy: {acc:.4f}")

        cls_report = metrics.classification_report(
            y_test, y_pred, target_names=self.class_names, digits=4
        )
        print("\nClassification report (test):")
        print(cls_report)

        self._save_confusion_and_per_class_acc(y_test, y_pred, suffix=self.model_type)

        # Save model + metrics
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = self.models_dir / f"{self.model_type}_{self.base_model_name}_{ts}.joblib"
        joblib.dump(model, model_path)
        print(f"\n[BaselineTrainer] Saved model -> {model_path}")

        metrics_dict = metrics.classification_report(
            y_test, y_pred, target_names=self.class_names, output_dict=True
        )
        metrics_dict["accuracy"] = acc
        meta = {
            "model_type": self.model_type,
            "base_model_name": self.base_model_name,
            "timestamp": ts,
            "metrics": metrics_dict,
        }
        metrics_path = self.models_dir / f"{self.model_type}_{self.base_model_name}_{ts}_metrics.json"
        with metrics_path.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"[BaselineTrainer] Saved metrics -> {metrics_path}")

    # ──────────────── CNN end-to-end (optional) ────────────────
    def _build_base_cnn(self):
        if self.base_model_name == "efficientnetb0":
            base = EfficientNetB0(
                include_top=False, weights="imagenet", pooling="avg", input_shape=(224, 224, 3)
            )
            preprocess_fn = eff_preprocess
        elif self.base_model_name == "resnet50":
            base = ResNet50(
                include_top=False, weights="imagenet", pooling="avg", input_shape=(224, 224, 3)
            )
            preprocess_fn = resnet_preprocess
        else:
            raise ValueError("base_model_name phải là 'efficientnetb0' hoặc 'resnet50'")
        return base, preprocess_fn

    def _make_cnn_generators(self, preprocess_fn):
        # Augmentation cho train, chỉ rescale cho val/test
        def add_noise(img):
            # img: numpy array [-?, +?] trước khi preprocess_fn
            noise = np.random.normal(0, 0.02, img.shape).astype(img.dtype)
            return img + noise

        train_datagen = ImageDataGenerator(
            preprocessing_function=lambda x: preprocess_fn(add_noise(x)),
            rotation_range=20,
            width_shift_range=0.1,
            height_shift_range=0.1,
            zoom_range=0.1,
            shear_range=0.1,
            horizontal_flip=True,
            brightness_range=(0.8, 1.2),
        )
        test_datagen = ImageDataGenerator(preprocessing_function=preprocess_fn)

        train_gen = train_datagen.flow_from_directory(
            self.processed_dir / "train",
            target_size=self.input_size,
            batch_size=self.batch_size,
            class_mode="categorical",
            shuffle=True,
            seed=self.seed,
        )
        val_gen = test_datagen.flow_from_directory(
            self.processed_dir / "val",
            target_size=self.input_size,
            batch_size=self.batch_size,
            class_mode="categorical",
            shuffle=False,
        )
        test_gen = test_datagen.flow_from_directory(
            self.processed_dir / "test",
            target_size=self.input_size,
            batch_size=self.batch_size,
            class_mode="categorical",
            shuffle=False,
        )
        return train_gen, val_gen, test_gen

    def train_eval_cnn(self):
        """
        Train CNN end-to-end với pretrained base + augmentation.
        """
        print("\n[BaselineTrainer][CNN] Building model...")
        base, preprocess_fn = self._build_base_cnn()
        base.trainable = False  # transfer learning cơ bản

        inputs = layers.Input(shape=(224, 224, 3))
        x = base(inputs, training=False)
        x = layers.Dropout(0.3)(x)
        outputs = layers.Dense(len(self.class_names), activation="softmax")(x)
        model = models.Model(inputs, outputs)

        opt = optimizers.Adam(learning_rate=1e-3)
        model.compile(optimizer=opt, loss="categorical_crossentropy", metrics=["accuracy"])

        train_gen, val_gen, test_gen = self._make_cnn_generators(preprocess_fn)

        print("\n[BaselineTrainer][CNN] Training...")
        history = model.fit(
            train_gen,
            validation_data=val_gen,
            epochs=self.epochs,
            verbose=1,
        )

        # Optional fine-tune: unfreeze toàn bộ base và train thêm với LR nhỏ
        if self.fine_tune:
            print("\n[BaselineTrainer][CNN] Fine-tuning base model...")
            base.trainable = True
            model.compile(
                optimizer=optimizers.Adam(learning_rate=1e-4),
                loss="categorical_crossentropy",
                metrics=["accuracy"],
            )
            ft_history = model.fit(
                train_gen,
                validation_data=val_gen,
                epochs=max(1, self.epochs // 2),
                verbose=1,
            )
            # nối history
            for k, v in ft_history.history.items():
                history.history.setdefault(k, [])
                history.history[k].extend(v)

        print("\n[BaselineTrainer][CNN] Evaluate on test set...")
        test_loss, test_acc = model.evaluate(test_gen, verbose=0)
        print(f"  Test accuracy: {test_acc:.4f}")

        # Confusion matrix + per-class acc
        y_true = test_gen.classes
        y_prob = model.predict(test_gen, verbose=0)
        y_pred = np.argmax(y_prob, axis=1)
        self._save_confusion_and_per_class_acc(y_true, y_pred, suffix=f"cnn_{self.base_model_name}")

        # Accuracy/loss curves
        plt.figure(figsize=(6, 4))
        plt.plot(history.history.get("accuracy", []), label="train_acc")
        if "val_accuracy" in history.history:
            plt.plot(history.history["val_accuracy"], label="val_acc")
        plt.xlabel("Epoch")
        plt.ylabel("Accuracy")
        plt.title("Accuracy Curve")
        plt.legend()
        acc_path = self.reports_dir / f"cnn_{self.base_model_name}_accuracy.png"
        plt.tight_layout()
        plt.savefig(acc_path, dpi=300)
        plt.close()

        plt.figure(figsize=(6, 4))
        plt.plot(history.history.get("loss", []), label="train_loss")
        if "val_loss" in history.history:
            plt.plot(history.history["val_loss"], label="val_loss")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.title("Loss Curve")
        plt.legend()
        loss_path = self.reports_dir / f"cnn_{self.base_model_name}_loss.png"
        plt.tight_layout()
        plt.savefig(loss_path, dpi=300)
        plt.close()

        print(f"  -> Saved accuracy curve: {acc_path}")
        print(f"  -> Saved loss curve: {loss_path}")

        # Save model + history
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_path = self.models_dir / f"cnn_{self.base_model_name}_{ts}.h5"
        model.save(model_path)
        print(f"[BaselineTrainer][CNN] Saved model -> {model_path}")

        hist_path = self.models_dir / f"cnn_{self.base_model_name}_{ts}_history.json"
        with hist_path.open("w", encoding="utf-8") as f:
            json.dump(history.history, f, ensure_ascii=False, indent=2)
        print(f"[BaselineTrainer][CNN] Saved history -> {hist_path}")


def main():
    # Ví dụ: train classical trên features
    trainer = BaselineTrainer(model_type="logreg")
    trainer.train_eval_classical()


if __name__ == "__main__":
    main()
