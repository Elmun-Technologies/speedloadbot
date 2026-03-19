import whisper
import os

# Lazy load model to avoid memory crash on import
_model = None

def get_model():
    global _model
    if _model is None:
        # Using base model for balance between speed and quality
        _model = whisper.load_model("base")
    return _model

def transcribe_video(file_path):
    try:
        model = get_model()
        result = model.transcribe(file_path)
        
        text_output = ""
        for segment in result['segments']:
            start = segment['start']
            # Format [mm:ss]
            mins, secs = divmod(int(start), 60)
            timestamp = f"[{mins:02d}:{secs:02d}]"
            text_output += f"{timestamp} {segment['text'].strip()}\n"
            
        return text_output
    except Exception as e:
        return f"Xatolik yuz berdi: {str(e)}"
