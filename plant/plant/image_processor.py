import cv2
import numpy as np
import os

def analyze_plant_health(image_path):
    """
    Analyze plant health from an image using color analysis
    
    Args:
        image_path: Path to the plant image
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            return {
                'status': 'Error',
                'disease_name': 'Invalid Image',
                'confidence': 0,
                'message': 'Could not read the image. Please check the file.'
            }
        
        # Check image size
        if img.size == 0:
            return {
                'status': 'Error',
                'disease_name': 'Empty Image',
                'confidence': 0,
                'message': 'Image appears to be empty or corrupted.'
            }
        
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for different disease indicators
        # Yellow/Brown range (Leaf Spot, Mildew)
        lower_yellow = np.array([15, 50, 50])
        upper_yellow = np.array([35, 255, 255])
        
        # Brown/Dark brown range (Blight, Rot)
        lower_brown = np.array([0, 20, 20])
        upper_brown = np.array([15, 255, 200])
        
        # Red/Rust range (Rust diseases)
        lower_red = np.array([0, 100, 100])
        upper_red = np.array([10, 255, 255])
        
        # Create masks for each disease indicator
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)
        mask_red = cv2.inRange(hsv, lower_red, upper_red)
        
        # Combine masks
        mask = mask_yellow + mask_brown + mask_red
        
        # Calculate disease percentage
        total_pixels = img.shape[0] * img.shape[1]
        disease_pixels = cv2.countNonZero(mask)
        severity = (disease_pixels / total_pixels) * 100 if total_pixels > 0 else 0
        
        # Calculate confidence (inverse of severity + base confidence)
        confidence = round(max(0, 100 - (severity / 2)), 2)
        
        # Classify based on severity
        if severity < 3:
            return {
                'status': 'Healthy',
                'disease_name': 'No Disease Detected',
                'confidence': confidence,
                'message': 'Your plant appears to be healthy! Continue with regular care and monitoring.'
            }
        elif severity < 10:
            return {
                'status': 'Non-Critical',
                'disease_name': 'Leaf Spot / Powdery Mildew',
                'confidence': confidence,
                'message': 'Minor infection detected. Recommended: Apply fungicide spray and improve air circulation.'
            }
        elif severity < 25:
            return {
                'status': 'Non-Critical',
                'disease_name': 'Early Blight / Rust',
                'confidence': confidence,
                'message': 'Moderate infection detected. Remove affected leaves and apply appropriate treatment.'
            }
        else:
            return {
                'status': 'Critical',
                'disease_name': 'Severe Blight / Rot',
                'confidence': confidence,
                'message': 'Critical infection detected! Immediate action needed: Isolate plant, remove affected parts, and apply strong fungicide.'
            }
            
    except Exception as e:
        return {
            'status': 'Error',
            'disease_name': 'Processing Error',
            'confidence': 0,
            'message': f'Error analyzing image: {str(e)}'
        }