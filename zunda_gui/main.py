import os.path
from pathlib import Path
from typing import Dict

import streamlit as st
import streamlit_ext as ste
from zunda_w import voice_vox
from zunda_w.main import Options, main

convert_option = Options(audio_files=['input'], )
download_voicevox = False


def get_speaker_info():
    voicevox_process = voice_vox.launch_voicevox_engine(voice_vox.extract_engine(root_dir=convert_option.engine_dir))
    voice_vox.get_speakers(convert_option.speaker_json)
    speakers = voice_vox.Speakers.read(convert_option.speaker_json)
    voicevox_process.terminate()
    voicevox_process.poll()
    return speakers


st.markdown(Path(os.path.abspath('BODY.md')).read_text(encoding='UTF-8'))
input_audio_file = st.file_uploader('音声ファイルのアップロード', type=['.wav', '.mp3'])
if not voice_vox.extract_engine(convert_option.engine_dir, dry_run=True):
    if st.button('Donwnload voicevox'):
        with st.spinner('Downloading Voicevox...'):
            voice_vox.extract_engine(convert_option.engine_dir, dry_run=False)
        download_voicevox = True
else:
    download_voicevox = True

if download_voicevox:
    speakers = get_speaker_info()
    speaker_name_view: Dict[int, str] = speakers.as_view()

    st.subheader('変換する話者を選択してください')
    speaker_id = st.selectbox('話者', options=list(speaker_name_view.keys()),
                              format_func=lambda key: speaker_name_view.get(key, 'No Choice'))
    convert_option.speakers = [speaker_id]
    merge_file = 'no_merge.wav'
    stt_file = 'no_data.stt'
    if input_audio_file and st.button('Start'):
        st.warning('It take a few minutes.')
        with open('input', 'wb') as fp:
            fp.write(input_audio_file.getvalue())
        with st.spinner('Processing...'):
            iterator = main(convert_option)
            st.text(next(iterator)[0])
            msg, stt_file = next(iterator)
            st.text(msg)
            msg, tts_dir = next(iterator)
            st.text(msg)
            st.text(next(iterator)[0])
            msg, merge_file = next(iterator)
            st.text(msg)

        # write upload file to local
    if os.path.exists(merge_file) and os.path.exists(stt_file):
        st.audio(merge_file)
        ste.download_button('Download wav',
                            data=Path(merge_file).read_bytes(),
                            file_name=merge_file,
                            mime='audio/wav')
        ste.download_button('Download srt',
                            data=Path(stt_file).read_bytes(),
                            file_name='transcribe.stt',
                            mime='text/plain',
                            )
        with st.expander('View STT'):
            st.code(Path(stt_file).read_text(encoding='UTF-8'))
