from flask import Flask, request

app = Flask(__name__)


@app.route("/detect", methods=["POST", "GET"])
def detect():

    import numpy as np
    import argparse
    import cv2
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Dropout, Flatten
    from tensorflow.keras.layers import Conv2D
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.layers import MaxPooling2D
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    import os
    import time
    happy=0
    sad=0
    large=0
    angry=0
    neutral=0
    surprise=0
    fear=0
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

    # command line argument
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode",help="train/display")
    a = ap.parse_args()
    mode = a.mode 

    def plot_model_history(model_history):
        """
        Plot Accuracy and Loss curves given the model_history
        """
        fig, axs = plt.subplots(1,2,figsize=(15,5))
        # summarize history for accuracy
        axs[0].plot(range(1,len(model_history.history['acc'])+1),model_history.history['acc'])
        axs[0].plot(range(1,len(model_history.history['val_acc'])+1),model_history.history['val_acc'])
        axs[0].set_title('Model Accuracy')
        axs[0].set_ylabel('Accuracy')
        axs[0].set_xlabel('Epoch')
        axs[0].set_xticks(np.arange(1,len(model_history.history['acc'])+1),len(model_history.history['acc'])/10)
        axs[0].legend(['train', 'val'], loc='best')
        # summarize history for loss
        axs[1].plot(range(1,len(model_history.history['loss'])+1),model_history.history['loss'])
        axs[1].plot(range(1,len(model_history.history['val_loss'])+1),model_history.history['val_loss'])
        axs[1].set_title('Model Loss')
        axs[1].set_ylabel('Loss')
        axs[1].set_xlabel('Epoch')
        axs[1].set_xticks(np.arange(1,len(model_history.history['loss'])+1),len(model_history.history['loss'])/10)
        axs[1].legend(['train', 'val'], loc='best')
        fig.savefig('plot.png')
        plt.show()

    # Define data generators
    train_dir = 'data/train'
    val_dir = 'data/test'

    num_train = 28709
    num_val = 7178
    batch_size = 64
    num_epoch = 50

    train_datagen = ImageDataGenerator(rescale=1./255)
    val_datagen = ImageDataGenerator(rescale=1./255)

    train_generator = train_datagen.flow_from_directory(
            train_dir,
            target_size=(48,48),
            batch_size=batch_size,
            color_mode="grayscale",
            class_mode='categorical')

    validation_generator = val_datagen.flow_from_directory(
            val_dir,
            target_size=(48,48),
            batch_size=batch_size,
            color_mode="grayscale",
            class_mode='categorical')

    # Create the model
    model = Sequential()

    model.add(Conv2D(32, kernel_size=(3, 3), activation='relu', input_shape=(48,48,1)))
    model.add(Conv2D(64, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Conv2D(128, kernel_size=(3, 3), activation='relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Flatten())
    model.add(Dense(1024, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(7, activation='softmax'))

    # If you want to train the same model or try other models, go for this
    if mode == "train":
        model.compile(loss='categorical_crossentropy',optimizer=Adam(lr=0.0001, decay=1e-6),metrics=['accuracy'])

        model_info = model.fit_generator(
                train_generator,
                steps_per_epoch=num_train // batch_size,
                epochs=num_epoch,
                validation_data=validation_generator,
                validation_steps=num_val // batch_size)

        plot_model_history(model_info)
        model.save_weights('model.h5')

    # emotions will be displayed on your face from the webcam feed
    elif mode == "display":
        model.load_weights('model.h5')

        # prevents openCL usage and unnecessary logging messages
        cv2.ocl.setUseOpenCL(False)

        # dictionary which assigns each label an emotion (alphabetical order)
        emotion_dict = {0: "Angry", 1: "Disgusted", 2: "Fearful", 3: "Happy", 4: "Neutral", 5: "Sad", 6: "Surprised"}

        # start the webcam feed
        cap = cv2.VideoCapture(0)
        for i in range(10):
            # Find haar cascade to draw bounding box around face
            ret, frame = cap.read()
            if not ret:
                break
            facecasc = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = facecasc.detectMultiScale(gray,scaleFactor=1.3, minNeighbors=5)

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y-50), (x+w, y+h+10), (255, 0, 0), 2)
                roi_gray = gray[y:y + h, x:x + w]
                cropped_img = np.expand_dims(np.expand_dims(cv2.resize(roi_gray, (48, 48)), -1), 0)
                prediction = model.predict(cropped_img)
                maxindex = int(np.argmax(prediction))
                cv2.putText(frame, emotion_dict[maxindex], (x+20, y-60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
                print(emotion_dict[maxindex])
                if emotion_dict[maxindex] == 'Angry':
                    angry+=1
                elif emotion_dict[maxindex] == 'Sad':
                    sad+=1
                elif emotion_dict[maxindex] == 'Happy':
                    happy+=1 
                elif emotion_dict[maxindex] == 'Fearful':
                    fear+=1
                elif emotion_dict[maxindex] == 'Surprised':
                    surprise+=1
                else :
                    neutral+=1  
            cv2.imshow('Video', cv2.resize(frame,(800,600),interpolation = cv2.INTER_CUBIC))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            time.sleep(0.5)
    if (angry > sad) and (angry > happy) and angry > fear and angry > surprise and angry > neutral:
        large = angry
        result = 0.47 
    elif (sad > angry) and (sad > happy) and sad > fear and sad >surprise and sad >neutral:
        large = sad
        result = 0.41
    elif happy > sad and happy > angry and happy >fear and happy >surprise and happy > neutral:
        large = happy
        result = 0.05
    elif surprise > sad and surprise > angry and surprise > fear and surprise > happy and surprise > neutral:
        large = surprise
        result = 0.15
    elif fear > sad and fear > angry and fear > happy and fear > surprise and fear > neutral:
        large = fear
        result= 0.25
    else:
        large = neutral
        result = 0    
    print(large)
    print(result)
    cap.release()
    cv2.destroyAllWindows()
    '''input is from webcam ,convert to a image from a directory .
    python3 emotions.py --mode display       is used to run the emotions.py in tensorflow folder'''


app.run(debug=True, host='192.168.42.125', port=8084)
