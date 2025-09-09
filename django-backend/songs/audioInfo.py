import os
import tempfile
from pydub import AudioSegment
from pydub.effects import speedup
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import numpy as np
import librosa
import soundfile as sf
from scipy import signal
import io

ffmpeg_path = os.path.join(settings.BASE_DIR, 'ffmpeg.exe')
os.environ['PATH'] = ffmpeg_path + os.pathsep + os.environ['PATH']

class AudioProcessor:
    """
    Class to handle audio processing operations including speed change,
    pitch correction, and audio effects.
    """
    
    @staticmethod
    def change_speed_pydub(audio_file_path, speed_factor=1.0, output_format='mp3'):
        """
        Change audio speed using pydub (simpler method)
        
        Args:
            audio_file_path: Path to the audio file
            speed_factor: 0.5 = half speed, 2.0 = double speed
            output_format: Output format (mp3, wav, etc.)
            
        Returns:
            processed_audio: AudioSegment object
            temp_file_path: Path to temporary processed file
        """
        try:
            # Load audio file
            audio = AudioSegment.from_file(audio_file_path)
            
            # Change speed
            if speed_factor != 1.0:
                # Method 1: Using frame rate manipulation (changes pitch)
                new_frame_rate = int(audio.frame_rate * speed_factor)
                processed_audio = audio._spawn(
                    audio.raw_data, 
                    overrides={'frame_rate': new_frame_rate}
                )
                processed_audio = processed_audio.set_frame_rate(audio.frame_rate)
                
                # Alternative: Use speedup effect (maintains pitch better for speedup)
                if speed_factor > 1.0:
                    processed_audio = speedup(processed_audio, playback_speed=speed_factor)
            
            else:
                processed_audio = audio
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{output_format}')
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Export processed audio
            processed_audio.export(temp_file_path, format=output_format)
            
            return processed_audio, temp_file_path
            
        except Exception as e:
            raise Exception(f"Audio processing failed: {str(e)}")
    
    @staticmethod
    def change_speed_librosa(audio_file_path, speed_factor=1.0, maintain_pitch=True):
        """
        Change audio speed using librosa (more advanced, better quality)
        
        Args:
            audio_file_path: Path to the audio file
            speed_factor: 0.5 = half speed, 2.0 = double speed
            maintain_pitch: Whether to maintain original pitch when changing speed
            
        Returns:
            processed_audio: Audio data as numpy array
            sample_rate: Sample rate of processed audio
            temp_file_path: Path to temporary processed file
        """
        try:
            # Load audio file
            y, sr = librosa.load(audio_file_path, sr=None)
            
            if maintain_pitch:
                # Time-stretch without changing pitch
                processed_audio = librosa.effects.time_stretch(y, rate=speed_factor)
                new_sr = sr  # Sample rate remains the same
            else:
                # Resample to change speed (changes pitch)
                new_sr = int(sr * speed_factor)
                processed_audio = librosa.resample(y, orig_sr=sr, target_sr=new_sr)
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Save processed audio
            sf.write(temp_file_path, processed_audio, new_sr if not maintain_pitch else sr)
            
            return processed_audio, new_sr if not maintain_pitch else sr, temp_file_path
            
        except Exception as e:
            raise Exception(f"Librosa audio processing failed: {str(e)}")
    
    @staticmethod
    def change_playback_speed(song_instance, speed_factor=1.0, method='librosa', maintain_pitch=True):
        """
        Main function to change playback speed of a song
        
        Args:
            song_instance: Django Song model instance
            speed_factor: Speed multiplier (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
            method: 'pydub' or 'librosa'
            maintain_pitch: Whether to maintain original pitch
            
        Returns:
            processed_audio_path: Path to the processed audio file
            duration: New duration in seconds
        """
        # Validate speed factor
        if not 0.25 <= speed_factor <= 4.0:
            raise ValueError("Speed factor must be between 0.25 and 4.0")
        
        # Get audio file path
        audio_file_path = song_instance.audio_file.path
        
        # Process based on selected method
        if method == 'pydub':
            processed_audio, temp_file_path = AudioProcessor.change_speed_pydub(
                audio_file_path, speed_factor, 'mp3'
            )
            new_duration = len(processed_audio) / 1000  # Convert ms to seconds
            
        elif method == 'librosa':
            processed_audio, new_sr, temp_file_path = AudioProcessor.change_speed_librosa(
                audio_file_path, speed_factor, maintain_pitch
            )
            new_duration = len(processed_audio) / new_sr if not maintain_pitch else len(processed_audio) / song_instance.audio_file.samplerate
            
        else:
            raise ValueError("Method must be 'pydub' or 'librosa'")
        
        return temp_file_path, new_duration
    
    @staticmethod
    def get_audio_info(audio_file_path):
        """
        Get detailed information about an audio file
        """
        try:
            audio = AudioSegment.from_file(audio_file_path)
            
            return {
                'duration_seconds': len(audio) / 1000,
                'channels': audio.channels,
                'sample_width': audio.sample_width,
                'frame_rate': audio.frame_rate,
                'frame_count': audio.frame_count(),
                'max_dBFS': audio.max_dBFS,
                'rms_dBFS': audio.rms_dBFS
            }
        except Exception as e:
            raise Exception(f"Failed to get audio info: {str(e)}")
    
    @staticmethod
    def generate_waveform(audio_file_path, width=800, height=200):
        """
        Generate waveform data for audio visualization
        """
        try:
            y, sr = librosa.load(audio_file_path, sr=None)
            
            # Simplify waveform for frontend display
            waveform = []
            chunk_size = len(y) // width
            
            for i in range(width):
                start = i * chunk_size
                end = min((i + 1) * chunk_size, len(y))
                if start < len(y):
                    chunk = y[start:end]
                    max_val = np.max(np.abs(chunk))
                    waveform.append(float(max_val))
            
            return {
                'waveform': waveform,
                'sample_rate': sr,
                'duration': len(y) / sr,
                'width': width,
                'height': height
            }
        except Exception as e:
            raise Exception(f"Failed to generate waveform: {str(e)}")


# Utility functions for easy access
def change_speed(song_instance, speed_factor=1.0, **kwargs):
    """
    Convenience function to change audio speed
    """
    return AudioProcessor.change_playback_speed(song_instance, speed_factor, **kwargs)


def get_song_duration(song_instance):
    """
    Get duration of a song in seconds
    """
    audio_file_path = song_instance.audio_file.path
    audio = AudioSegment.from_file(audio_file_path)
    return len(audio) / 1000


def create_speed_variants(song_instance, speed_factors=[0.75, 1.0, 1.25, 1.5]):
    """
    Create multiple speed variants of a song
    """
    variants = {}
    
    for speed_factor in speed_factors:
        try:
            temp_path, duration = change_speed(song_instance, speed_factor)
            variants[speed_factor] = {
                'temp_path': temp_path,
                'duration': duration
            }
        except Exception as e:
            print(f"Failed to create speed variant {speed_factor}: {str(e)}")
    
    return variants