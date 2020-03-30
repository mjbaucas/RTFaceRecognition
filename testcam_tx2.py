import cv2
from numpy import load, expand_dims, asarray
from sklearn.preprocessing import Normalizer, LabelEncoder
from sklearn.svm import SVC
from random import choice
from frame_utils import get_embedding, extract_face_from_frame, readjust_coordinates
from keras.models import load_model

#################################################################
# Pre-load Model 
################################################################# 
data = load('5-celebrity-faces-embeddings.npz')
trainX = data['arr_0']
trainY = data['arr_1']

encode_in = Normalizer(norm='l2')

nsamples, nx, ny = trainX.shape
trainX = trainX.reshape((nsamples,nx*ny))

model_facenet = load_model('facenet_keras.h5')
trainX = encode_in.transform(trainX)

encode_out = LabelEncoder()
encode_out.fit(trainY)

trainY = encode_out.transform(trainY)
model = SVC(kernel='linear', probability=True)
model.fit(trainX, trainY)

#################################################################
# Open Camera 
################################################################# 
xml_path = "haarcascade_frontalface_default.xml"
face_detector = cv2.CascadeClassifier(xml_path)

#gst_str = "nvcamerasrc ! video/x-raw(memory:NVMM), width=(int)1280, height=(int)720,format=(string)I420, framerate=(fraction)30/1 ! nvvidconv flip-method=0 ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! appsink"
#capture = cv2.VideoCapture(gst_str, cv2.CAP_GSTREAMER)
capture = cv2.VideoCapture(0)


min_width = 30
min_height = 30

font = cv2.FONT_HERSHEY_DUPLEX
rec_color = (0, 255, 0)

#################################################################
# Detection and Classification Loop
#################################################################
predicted_name = "Stranger"
 
while True:
	__, frame = capture.read()
	frame = cv2.resize(frame, (640, 480)) 
	ret, img, coord = extract_face_from_frame(face_detector, frame)
	if ret == 0:
		x1, x2, y1, y2 = coord
		testX = asarray(get_embedding(model_facenet, img))

		nx, ny = testX.shape
		testX = testX.reshape((-1, nx*ny))

		yhat_class = model.predict(testX)
		yhat_prob = model.predict_proba(testX)

		class_index = yhat_class[0]
		class_probability = yhat_prob[0,class_index] * 100
		predicted_name = encode_out.inverse_transform(yhat_class)[0]
		#print('Predicted: %s (%.3f)' % (predict_names[0], class_probability))

		# Draw
		cv2.rectangle(frame, (x1, y1), (x2, y2), rec_color, 2)
		
		# Put label
		cv2.rectangle(frame, (x1, y1 - 10), (x2, y1), (0, 0, 255), cv2.FILLED)
		cv2.putText(frame, predicted_name, (x1 + 3, y1 - 3), font, 0.3, (255, 255, 255), 1)

	cv2.imshow('Video', frame)
	key = cv2.waitKey(1) & 0xFF
	
	#capture.truncate(0)
	# Exit
	if key == ord('q'):
		break

# Release webcam handle
capture.release()
cv2.destroyAllWindows()
