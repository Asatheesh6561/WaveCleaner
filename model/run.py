import time
import os
import glob
import os
import argparse
import torch
from librosa.util import normalize
from scipy.io.wavfile import write
from dataset import MAX_WAV_VALUE, load_wav
from generator import BNEGenerator
from utils import HParam

def load_checkpoint(filepath, device):
    assert os.path.isfile(filepath)
    print("Loading '{}'".format(filepath))
    checkpoint_dict = torch.load(filepath, map_location=device)
    print("Complete.")
    return checkpoint_dict

def scan_checkpoint(cp_dir, prefix):
    pattern = os.path.join(cp_dir, prefix + '*')
    cp_list = glob.glob(pattern)
    if len(cp_list) == 0:
        return ''
    return sorted(cp_list)[-1]

def inference(with_postnet=False):
    generator = BNEGenerator(hp.model.in_channels).to(device)

    state_dict_g = load_checkpoint("g_00370000", device)
    generator.load_state_dict(state_dict_g['generator'])

    filelist = os.listdir("in")

    os.makedirs("out", exist_ok=True)

    generator.eval()
    #generator.remove_weight_norm()
    with open('filenames.txt') as f:
        filenames = [line.strip() for line in f]
    with torch.no_grad():
        for filename in filenames:
            wav, sr = load_wav(os.path.join("in", filename))
            wav = wav / MAX_WAV_VALUE
            wav = normalize(wav) * 0.95
            wav = torch.FloatTensor(wav)
            wav = wav.reshape((1, 1, wav.shape[0],)).to(device)
            before_y_g_hat, y_g_hat = generator(wav, with_postnet)
            audio = before_y_g_hat.reshape((before_y_g_hat.shape[2],))
            audio = audio * MAX_WAV_VALUE
            audio = audio.cpu().numpy().astype('int16')
            output_file = os.path.join("out", os.path.splitext(filename)[0] + '_generated.wav')
            write(output_file, hp.audio.sampling_rate, audio)

            print(output_file)
def main():
    start = time.perf_counter()
    print('Initializing Inference Process..')

    parser = argparse.ArgumentParser()
    parser.add_argument('--input_wavs_dir', default='test_files')
    parser.add_argument('--output_dir', default='generated_files')
    parser.add_argument('--checkpoint_file', required=False)
    parser.add_argument('-c', '--config', default='config.yaml')


    args = parser.parse_args()

    global hp
    hp = HParam(args.config)
    with open(args.config, 'r') as f:
        hp_str = ''.join(f.readlines())

    torch.manual_seed(hp.train.seed)
    global device
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    print(device)
    inference()
    stop = time.perf_counter()
    print(stop-start)
main()