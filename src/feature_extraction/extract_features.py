import json
from pathlib import Path
from typing import Tuple

import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import EfficientNetB0, ResNet50
from tensorflow.keras.applications.efficientnet import preprocess_input as eff_preprocess
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess


class FeatureExtractor:
    """
    Trích xuất vector đặc trưng từ ảnh đã resize (data/processed)
    bằng CNN pretrained (EfficientNetB0 / ResNet50), lưu ra .npy.
    """

    def __init__(
        self,
        base_model_name: str = "efficientnetb0",
        processed_dir: str = "data/processed",
        output_dir: str = "data/features",
        batch_size: int = 32,
        seed: int = 42,
    ):
        self.base_model_name = base_model_name.lower()
        self.processed_dir = Path(processed_dir)
        self.output_dir = Path(output_dir) / self.base_model_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.batch_size = batch_size
        self.seed = seed

        self.input_size = (224, 224)
        self.base_model, self.preprocess_fn = self._build_base_model()

    def _build_base_model(self):
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
        base.trainable = False
        return base, preprocess_fn

    def _make_generator(self, split: str):
        datagen = ImageDataGenerator(preprocessing_function=self.preprocess_fn)
        split_dir = self.processed_dir / split
        if not split_dir.is_dir():
            raise FileNotFoundError(f"Không tìm thấy thư mục ảnh: {split_dir}")
        gen = datagen.flow_from_directory(
            split_dir,
            target_size=self.input_size,
            batch_size=self.batch_size,
            class_mode="sparse",
            shuffle=False,  # đảm bảo thứ tự labels trùng với features
            seed=self.seed,
        )
        return gen

    def _extract_split(self, split: str) -> Tuple[np.ndarray, np.ndarray, dict]:
        gen = self._make_generator(split)
        n_samples = gen.samples
        steps = int(np.ceil(n_samples / self.batch_size))
        feats = self.base_model.predict(gen, steps=steps, verbose=1)
        labels = gen.classes.astype(np.int64)
        class_indices = gen.class_indices
        return feats, labels, class_indices

    def extract_and_save_all(self):
        """
        Extract features cho train/val/test, lưu:
        - features_{split}.npy
        - labels_{split}.npy
        - class_indices.json
        """
        all_class_indices = None
        for split in ["train", "val", "test"]:
            print(f"\n[FeatureExtractor] Extracting '{split}' với {self.base_model_name}...")
            feats, labels, class_indices = self._extract_split(split)
            if all_class_indices is None:
                all_class_indices = class_indices

            np.save(self.output_dir / f"features_{split}.npy", feats)
            np.save(self.output_dir / f"labels_{split}.npy", labels)
            print(
                f"  -> Saved: {self.output_dir / f'features_{split}.npy'} "
                f"({feats.shape[0]} x {feats.shape[1]})"
            )

        # Lưu mapping class_indices một lần
        if all_class_indices is not None:
            with (self.output_dir / "class_indices.json").open("w", encoding="utf-8") as f:
                json.dump(all_class_indices, f, ensure_ascii=False, indent=2)
            print(f"\n[FeatureExtractor] Saved class_indices -> {self.output_dir / 'class_indices.json'}")


def main():
    extractor = FeatureExtractor()
    extractor.extract_and_save_all()


if __name__ == "__main__":
    main()
