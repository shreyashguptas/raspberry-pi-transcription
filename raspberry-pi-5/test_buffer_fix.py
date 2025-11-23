#!/usr/bin/env python3
"""
Test if holding a reference to the mel buffer fixes the issue
"""

import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.expanduser('~/Hailo-Application-Code-Examples/runtime/hailo-8/python/speech_recognition'))

from hailo_platform import HEF, VDevice, HailoSchedulingAlgorithm, FormatType
from common.audio_utils import load_audio
from common.preprocessing import preprocess
from app.whisper_hef_registry import HEF_REGISTRY


def get_hef_path(model_variant, hw_arch, component):
    base_path = os.path.expanduser('~/Hailo-Application-Code-Examples/runtime/hailo-8/python/speech_recognition')
    return os.path.join(base_path, HEF_REGISTRY[model_variant][hw_arch][component])


def main():
    print("="*70)
    print("  BUFFER REFERENCE FIX TEST")
    print("="*70)
    print("")

    variant = "tiny"
    hw_arch = "hailo8l"

    encoder_path = get_hef_path(variant, hw_arch, "encoder")
    decoder_path = get_hef_path(variant, hw_arch, "decoder")

    audio_path = "/tmp/seg_1.wav"

    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return

    # Load and preprocess
    print("Loading and preprocessing audio...")
    audio = load_audio(audio_path)
    mel_spectrograms = preprocess(audio, is_nhwc=True, chunk_length=10, chunk_offset=0)
    mel = mel_spectrograms[0]

    print(f"Original mel shape: {mel.shape}")
    print("")

    # Prepare mel (same as pipeline does)
    if mel.ndim == 4 and mel.shape[1] == 1:
        mel = mel.squeeze(1)

    # CRITICAL: Create owned, contiguous copy and HOLD THE REFERENCE
    mel_buffer = np.ascontiguousarray(mel)

    print(f"Prepared mel shape: {mel_buffer.shape}")
    print(f"Prepared mel dtype: {mel_buffer.dtype}")
    print(f"Prepared mel nbytes: {mel_buffer.nbytes}")
    print(f"C-contiguous: {mel_buffer.flags['C_CONTIGUOUS']}")
    print(f"OWNDATA: {mel_buffer.flags['OWNDATA']}")
    print("")

    # Create VDevice and run inference (synchronous, no threading)
    params = VDevice.create_params()
    params.scheduling_algorithm = HailoSchedulingAlgorithm.ROUND_ROBIN

    with VDevice(params) as vdevice:
        encoder_infer_model = vdevice.create_infer_model(encoder_path)
        encoder_infer_model.input().set_format_type(FormatType.FLOAT32)
        encoder_infer_model.output().set_format_type(FormatType.FLOAT32)

        with encoder_infer_model.configure() as configured:
            bindings = configured.create_bindings()

            # Set input buffer - KEEP REFERENCE
            print("Setting input buffer...")
            bindings.input().set_buffer(mel_buffer)

            # Create output buffer
            output_buffer = np.zeros(encoder_infer_model.output().shape, dtype=np.float32)
            bindings.output().set_buffer(output_buffer)

            print("Running inference...")
            try:
                configured.run([bindings], 100000)  # 100 second timeout
                print("✓ Inference SUCCESSFUL!")
                print(f"Output shape: {output_buffer.shape}")
                print(f"Output sample: {output_buffer[0, 0, :5]}")
            except Exception as e:
                print(f"❌ Inference FAILED: {e}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
