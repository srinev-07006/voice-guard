import librosa
from transformers import pipeline

class VoiceCloneDetector:
    def __init__(self):
        print("Loading AI model into memory... (This takes a moment)")
        self.pipe = pipeline(
            "audio-classification", 
            model="Hemgg/Deepfake-audio-detection"
        )
        print("Model loaded successfully!")

    def analyze_audio(self, audio_input):
        """
        Accepts a file path string or a preprocessed payload dictionary.
        Returns the probability (0.0 to 1.0) that the voice is synthetic.
        """
        try:
            if isinstance(audio_input, str):
                audio_data, sampling_rate = librosa.load(audio_input, sr=16000, mono=True)
                payload = {"raw": audio_data, "sampling_rate": sampling_rate}
            else:
                payload = audio_input

            results = self.pipe(payload)
            print(f"Raw model output: {results}") 
            
            # Generalized check for synthetic speech labels
            synthetic_keywords = ['fake', 'spoof', 'ai', 'synthetic']
            for result in results:
                label_lower = result['label'].lower()
                if any(keyword in label_lower for keyword in synthetic_keywords):
                    return result['score']
                    
            return 0.0
            
        except Exception as e:
            print(f"Error processing audio: {e}")
            return None


if __name__ == "__main__":
    detector = VoiceCloneDetector()
    
    test_audio = r"D:\Projects\VeriVoice\audios\real\sample2.wav" 
    
    risk_score = detector.analyze_audio(test_audio)
    
    if risk_score is not None:
        print(f"⚠️ Deepfake Probability Score: {risk_score * 100:.2f}%")
    else:
        print("Analysis failed. Please verify the audio file format and path.")