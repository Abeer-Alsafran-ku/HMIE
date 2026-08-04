# Spatially Guided Image Selection for Efficient Deep Learning Dataset Construction

---

# Abstract

## Objective
Large aerial image datasets often contain significant spatial redundancy, resulting in increased storage requirements, longer training times, and unnecessary computational costs. This paper proposes a spatial image selection framework that utilizes image ground coverage estimation to identify representative training images while minimizing overlap.

## Method
The proposed approach estimates the ground footprint of each image using:

- UAV altitude
- Camera field of view (FOV)
- Image dimensions
- GPS location

The estimated footprints are used to compute spatial overlap between images, allowing redundant images to be removed before model training.

## Results
The selected subset is evaluated against random and baseline sampling approaches using dataset reduction, computational cost, and model performance metrics.

---

# 1. Introduction

## 1.1 Background

Modern UAVs can capture thousands of high-resolution images during a single flight. Although these datasets provide comprehensive scene coverage, they often contain substantial spatial redundancy due to overlapping image footprints.

Training deep learning models on redundant images increases:

- Storage requirements
- Labeling effort
- Training time
- Computational cost

without necessarily improving model accuracy.

---

## 1.2 Problem Statement

Traditional dataset selection techniques frequently rely on:

- Random sampling
- Temporal ordering
- Uniform interval selection

These approaches ignore the spatial relationships among captured images, leading to inefficient training datasets.

---

## 1.3 Research Objectives

The objectives of this work are:

- Estimate the ground coverage of every image.
- Represent each image as a geographic footprint.
- Measure spatial overlap between neighboring images.
- Select representative images with minimal redundancy.
- Evaluate the effect of spatial selection on deep learning performance.

---

## 1.4 Contributions

The main contributions are:

1. A mathematical framework for estimating image ground coverage.
2. A spatial image selection algorithm based on image footprints.
3. An overlap-aware redundancy reduction strategy.
4. Experimental validation demonstrating reduced dataset size while maintaining model performance.

---

# 2. Related Work

## 2.1 Dataset Reduction

Review methods including:

- Random Sampling
- Uniform Sampling
- Core-set Selection
- Active Learning
- Diversity Sampling

Discuss their advantages and limitations.

---

## 2.2 UAV Image Selection

Discuss previous work on:

- UAV mapping
- Flight planning
- Image overlap
- Photogrammetry
- Remote sensing datasets

---

## 2.3 Spatial Sampling

Review techniques involving:

- Spatial clustering
- Geographic indexing
- Coverage optimization
- Spatial diversity

---

## 2.4 Research Gap

Most existing image selection methods emphasize image appearance or feature similarity while neglecting the spatial distribution and geographic coverage of images.

This work addresses this gap by explicitly incorporating image ground coverage into the selection process.

---

# 3. Proposed Method

## 3.1 Dataset Description

Describe:

- UAV platform
- Camera specifications
- Number of images
- Flight altitude
- Image resolution
- GPS accuracy

---

## 3.2 Ground Coverage Estimation

For each image, estimate its ground footprint using:

### Inputs

- Altitude
- Horizontal FOV
- Vertical FOV
- Image width
- Image height
- GPS location

### Horizontal Ground Coverage

\[
W_g = 2H\tan\left(\frac{FOV_h}{2}\right)
\]

### Vertical Ground Coverage

\[
L_g = 2H\tan\left(\frac{FOV_v}{2}\right)
\]

### Ground Footprint Area

\[
A = W_g \times L_g
\]

where

- \(H\) = altitude
- \(FOV_h\) = horizontal field of view
- \(FOV_v\) = vertical field of view

---

## 3.3 Geographic Footprint Generation

Each image is represented by:

- Center GPS coordinate
- Ground footprint polygon
- Bounding box

This representation enables efficient spatial comparison among images.

---

## 3.4 Spatial Overlap Estimation

For neighboring images, compute the overlap ratio:

\[
Overlap =
\frac{Area_{intersection}}
{Area_{union}}
\]

Alternative metrics include:

- Percentage overlap
- Intersection-over-Union (IoU)
- Coverage redundancy

---

## 3.5 Spatial Image Selection Algorithm

### Step 1

Estimate ground coverage.

### Step 2

Generate geographic footprint.

### Step 3

Find neighboring images.

### Step 4

Calculate overlap.

### Step 5

Discard highly redundant images.

### Step 6

Retain representative images.

---

### Algorithm

```text
Input:
    Image dataset

For each image

    Compute ground footprint

Sort images

For each image

    Compute overlap with selected images

    If overlap < threshold

        Keep image

    Else

        Remove image

Return selected dataset
```

---

### Workflow Diagram

```
Images
    │
    ▼
Ground Coverage Estimation
    │
    ▼
Geographic Footprints
    │
    ▼
Spatial Overlap Analysis
    │
    ▼
Representative Image Selection
    │
    ▼
Training Dataset
```

---

# 4. Experimental Setup

## Dataset

Describe:

- Number of images
- Area covered
- Flight altitude
- Camera parameters

---

## Deep Learning Model

Specify:

- Network architecture
- Framework
- Optimizer
- Learning rate
- Epochs
- Batch size

---

## Hardware

Include:

- CPU
- GPU
- RAM
- Software versions

---

# 5. Evaluation Metrics

## Dataset Reduction

\[
Reduction =
\frac{N_{original}-N_{selected}}
{N_{original}}
\times100
\]

---

## Computational Metrics

- Training time
- GPU memory usage
- Storage reduction

---

## Model Performance

Evaluate using:

- Accuracy
- Precision
- Recall
- F1-score
- mAP (if object detection)

---

## Spatial Metrics

Evaluate:

- Average overlap
- Coverage percentage
- Spatial diversity
- Redundancy ratio

---

# 6. Results

## 6.1 Dataset Reduction

| Method | Images | Reduction |
|---------|--------|-----------|
| Original | | |
| Random Sampling | | |
| Proposed Method | | |

---

## 6.2 Model Performance

| Method | Accuracy | Precision | Recall | F1 |
|---------|----------|-----------|--------|----|
| Original | | | | |
| Random | | | | |
| Proposed | | | | |

---

## 6.3 Computational Cost

| Method | Training Time | GPU Memory | Storage |
|---------|---------------|------------|----------|
| Original | | | |
| Proposed | | | |

---

## 6.4 Spatial Visualization

Include figures showing:

- Original image footprints
- Selected images
- Removed images
- Geographic coverage map

---

# 7. Discussion

## Advantages

- Reduced spatial redundancy
- Faster model training
- Lower storage requirements
- Improved geographic diversity
- Better utilization of representative samples

---

## Limitations

- GPS positioning errors
- Assumption of level terrain
- Fixed overlap threshold
- Camera orientation uncertainty

---

## Future Improvements

- Adaptive overlap thresholds
- Terrain-aware footprint estimation
- Feature-aware spatial selection
- Active learning integration
- Multi-flight dataset fusion

---

# 8. Conclusion

This paper presented a spatial image selection framework that estimates image ground coverage using camera geometry and geographic information. The proposed method constructs geographic footprints, measures spatial overlap, and removes redundant images before deep learning training. Experimental results demonstrate that the proposed strategy significantly reduces dataset size and computational cost while maintaining comparable or improved model performance.

---

# Suggested Figures

1. UAV image acquisition geometry
2. Camera field of view
3. Ground footprint estimation
4. Geographic image footprints
5. Image overlap illustration
6. Proposed algorithm flowchart
7. Spatial distribution of selected images
8. Performance comparison charts

---

# Suggested Tables

| Table | Description |
|---------|-------------|
| Table 1 | Dataset characteristics |
| Table 2 | Camera parameters |
| Table 3 | Ground coverage examples |
| Table 4 | Selection thresholds |
| Table 5 | Experimental settings |
| Table 6 | Dataset reduction results |
| Table 7 | Performance comparison |
| Table 8 | Computational cost analysis |

---

# Potential Research Questions

- Can spatial redundancy be effectively reduced using ground coverage estimation?
- How much can the training dataset be reduced without degrading model performance?
- Does spatially guided image selection outperform random sampling?
- What overlap threshold provides the best trade-off between dataset size and model accuracy?
- How does spatial diversity influence deep learning generalization?

---

# Novelty Statement

The proposed framework introduces a **geometry-driven spatial image selection strategy** that leverages image ground coverage and geographic footprints to minimize spatial redundancy. Unlike conventional random or feature-based sampling methods, the proposed approach explicitly accounts for the spatial distribution of aerial imagery, enabling the construction of compact yet representative training datasets that reduce computational cost while preserving predictive performance.
