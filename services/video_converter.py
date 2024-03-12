import logging
import os
import subprocess


def convert_video_gif(scale, skip_first_n_secs, max_length_secs, input_video, output_gif):
    logging.info('convert_video_gif scale %i skip_first_n_secs %i max_length_secs %i input_video %s output_gif %s',
                 scale, skip_first_n_secs, max_length_secs, input_video, output_gif)

    retcode = subprocess.call([
        "ffmpeg", "-stats", "-i", input_video, "-vf",
        "fps=15,scale={}:-1:flags=lanczos".format(scale),
        "-ss", "00:00:" + "{}".format(skip_first_n_secs).zfill(2), "-t", "{}".format(max_length_secs), "-y",
        str(output_gif)
    ])
    os.remove(input_video)
    return retcode
