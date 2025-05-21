# Pokemon TCG Scanner

## Description

Pokemon TCG Scanner is a Python-based tool designed to detect, segment, crop, and identify Pokémon Trading Card Game (TCG) cards using computer vision techniques. The system supports individual images, video files, and real-time webcam input. It uses segmentation masks and perspective transformations to extract card regions, computes perceptual hashes, and compares them to a known dataset for identification. A graphical interface is provided for ease of use.

## Motivation

The motivation behind this project is to simplify and automate the process of recognizing Pokémon TCG cards. Whether you're managing a collection, developing a card-related app, or just curious, this tool provides a reliable and intuitive way to analyze and identify cards in various formats (images, videos, or live feed).

## Features

* Real-time card detection via webcam.

* Support for image and video inputs.

* Accurate card segmentation using masks and contours.

* Perspective correction and cropping for consistent identification.

* Image hashing (dHash + pHash) for matching with a card database.

* Flipped card detection for improved accuracy.

* Similarity scoring with threshold matching.

* Card tracking across frames using IoU-based logic.

* Tkinter GUI interface for ease of use.

* Overlay with bounding boxes, segmentation contours, and matched labels.

## Requirements

* Python 3.x

* Required libraries: 

    ![Pandas](https://img.shields.io/badge/Pandas-gray?style=flat&logo=Pandas) ![Numpy](https://img.shields.io/badge/Numpy-gray?style=flat&logo=Numpy) ![Ultralytics](https://img.shields.io/badge/Ultralytics-gray?style=flat&logo=Ultralytics) ![OpenCV](https://img.shields.io/badge/OpenCV-gray?style=flat&logo=OpenCV) ![Pillow](https://img.shields.io/badge/Pillow-gray?style=flat&logo=Pillow) ![Pytorch](https://img.shields.io/badge/Pytorch-gray?style=flat&logo=Pytorch) ![Imagehash](https://img.shields.io/badge/Imagehash-gray?style=flat&logo=Imagehash) ![Tkinter](https://img.shields.io/badge/Tkinter-gray?style=flat&logo=Tkinter)

## How to use

The workflow of the tool includes the following steps:

1. Load Dataset

    * A CSV file containing precomputed perceptual hashes (dHash + pHash) of known Pokémon cards is required.

    * Format must include columns: Name, Set_Name, Local_ID, and hash.

2. Start the GUI

    * Run the main script and choose one of the following:

        * Real-time camera input

        * Image input

        * Video input

3. Process

    * For each input frame:

        * Card segmentation is applied.

        * Valid card contours (approximated as quadrilaterals) are identified.

        * Perspective transformation crops the card to a standard size.
        
        * Hashes are computed for both the original and flipped versions.

        * Matching is performed against the dataset using Hamming distance.

        * If the similarity is under a set threshold, a match is declared.

        * Bounding boxes, segmentation contours, and card information are drawn on the frame.

4. Tracking

    * Detected cards are tracked between frames using IoU to maintain consistent identification over time.

5. Display

    * The processed frames are displayed on a GUI window using Tkinter.


## Examples of use

![](example.gif)