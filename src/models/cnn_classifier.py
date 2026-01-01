"""
CNN Model for Traffic Sign Classification
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2


def create_simple_cnn(input_shape=(64, 64, 3), num_classes=4):
    """
    Tạo simple CNN model
    Architecture: Conv -> Pool -> Conv -> Pool -> Dense
    """
    model = models.Sequential([
        # Input layer
        layers.Input(shape=input_shape),
        
        # Conv Block 1
        layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Conv Block 2
        layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Conv Block 3
        layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
        layers.BatchNormalization(),
        layers.MaxPooling2D((2, 2)),
        layers.Dropout(0.25),
        
        # Flatten and Dense
        layers.Flatten(),
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    return model


def create_transfer_learning_model(input_shape=(64, 64, 3), num_classes=4):
    """
    Tạo model sử dụng Transfer Learning với MobileNetV2
    Lightweight và phù hợp cho traffic sign classification
    """
    # Load pre-trained MobileNetV2
    base_model = MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights='imagenet'
    )
    
    # Freeze base model
    base_model.trainable = False
    
    # Add custom top layers
    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),
        layers.Dropout(0.5),
        layers.Dense(num_classes, activation='softmax')
    ])
    
    return model, base_model


def compile_model(model, learning_rate=0.001):
    """Compile model với optimizer và loss function"""
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss='categorical_crossentropy',
        metrics=['accuracy', 
                 keras.metrics.Precision(name='precision'),
                 keras.metrics.Recall(name='recall')]
    )
    return model


if __name__ == '__main__':
    # Test model creation
    print("🧪 Testing model creation...")
    
    print("\n1. Simple CNN:")
    simple_model = create_simple_cnn(num_classes=4)
    simple_model.summary()
    
    print("\n2. Transfer Learning (MobileNetV2):")
    transfer_model, _ = create_transfer_learning_model(num_classes=4)
    transfer_model.summary()
    
    print("\n✓ Models created successfully!")
