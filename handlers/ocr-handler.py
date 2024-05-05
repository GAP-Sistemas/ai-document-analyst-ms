import json
import boto3
import pytesseract
import os
import io
from PIL import Image

def generate_rotated_key(key):
    # Define a list of supported image formats
    supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']
    
    # Get the file extension
    _, ext = os.path.splitext(key)
    
    # Check if the file is an image based on the extension
    if ext.lower() in supported_formats:
        # Generate a new key for the rotated image
        rotated_key = key.rsplit(ext, 1)[0] + '-rotated' + ext
        return rotated_key
    else:
        raise ValueError("Unsupported file format")

def rotate_image(event, context):
    # Initialize S3 client
    print('event', event)
    print('event2', event)

    s3_client = boto3.client('s3')
    
    # Define the bucket name
    bucket_name = os.environ['BUCKET_NAME']

    #   # Check if 'body' is in event and it contains 'keys'
    # if 'body' not in event or 'keys' not in json.loads(event):
    #     return {
    #         "statusCode": 400,
    #         "body": json.dumps({"error": "Missing 'body' or 'keys' field in the event payload"})
    #     }
    
    # Parse the incoming JSON payload to get the keys array
    request_body = event
    # print('request_body', request_body)
    keys = request_body['body']['keys']
    print('keys', keys)

    # List to store the results
    processed_keys = []

    # Process each image
    for key in keys:
        try:
            # Get the object from S3
            response = s3_client.get_object(Bucket=bucket_name, Key=key)
            image_file = response['Body'].read()

            # Load the image from bytes
            image = Image.open(io.BytesIO(image_file))

            # Use pytesseract to detect orientation and script
            osd = pytesseract.image_to_osd(image)
            rotation_angle = int(osd.split('Rotate: ')[1].split('\n')[0])

            # Rotate the image if needed
            if rotation_angle != 0:
                rotated_image = image.rotate(-rotation_angle, expand=True)
                rotated_image_stream = io.BytesIO()
                rotated_image.save(rotated_image_stream, format=image.format)
                rotated_image_stream.seek(0)
                rotated_key = generate_rotated_key(key)
                s3_client.upload_fileobj(rotated_image_stream, bucket_name, rotated_key)
                processed_keys.append({"original_key": key, "new_key": rotated_key, "rotated": True})
            else:
                processed_keys.append({"original_key": key, "new_key": key, "rotated": False})
        except ValueError as e:
            processed_keys.append({"key": key, "error": str(e), "rotated": False})
        except Exception as e:
            processed_keys.append({"key": key, "error": str(e), "rotated": False})

    # Create response with processed keys info
    response = {
        "statusCode": 200,
        "body": json.dumps({"processed_keys": processed_keys})
    }

    return response

# Example event data for testing
# event = {
#     "body": json.dumps({"keys": ["converted-images-for-ai/4k8AmxWnS-cert_virado.pdf.2-rotated.png","converted-images-for-ai/4k8AmxWnS-cert_virado.pdf.2.png"]})
# }
# context = {}

# serverless invoke local --function ocr --data '{"body": {"keys": ["converted-images-for-ai/4k8AmxWnS-cert_virado.pdf.2-rotated.png","converted-images-for-ai/4k8AmxWnS-cert_virado.pdf.2.png"]}}'

# # Example function call
# output = rotate_image(event, context)
# print(output)
