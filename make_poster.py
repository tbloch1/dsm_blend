import argparse
import subprocess
from glob import glob
import matplotlib.pyplot as plt
import matplotlib.image as mpimg


def add_rockwell_font():
    from matplotlib import font_manager

    font_path = 'font/ROCK.TTF'  # Your font path goes here
    font_manager.fontManager.addfont(font_path)
    prop = font_manager.FontProperties(fname=font_path)

    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = prop.get_name()


def do_plotting(location):
    
    plt.style.use('dark_background')

    img = mpimg.imread('render.png')

    fig = plt.figure(figsize=(54, 54 * 3/7), dpi=200)
    axs = [plt.subplot(1,1,1)]

    axs[0].imshow(img)

    if len(glob('*signature*')) == 1:

        left, bottom, width, height = [0.84, 0.08, 0.05, 0.0325]
        ax2 = fig.add_axes([left, bottom, width, height])
        axs += [ax2]
        sig = 'signature.png'
        img = mpimg.imread(sig)
        axs[-1].imshow(img)

    filename = glob('data/20*')[0]
    year = filename.split('/')[-1].split('_')[0]
    plot_text = f'{location} and Surrounding Area, {year}.'

    plt.text(0.51, 0.085, plot_text,
            fontdict = {
                'fontname': 'Rockwell',
                'fontsize': '28',
                # 'fontweight' : 'bold',
                'verticalalignment': 'baseline',
                'horizontalalignment': 'center'},
            transform=plt.gcf().transFigure)

    [ax.axis('off') for ax in axs]
    plt.savefig(f'poster_{location.lower().replace(" ", "_")}.pdf', bbox_inches='tight', pad_inches=0.5)
    plt.close()
    print(f'Poster saved: poster_{location.lower().replace(" ", "_")}.pdf')


def rgb_2cmyk(location):
    rgb_pdf = f'poster_{location.lower().replace(" ", "_")}.pdf'
    cmyk_pdf = rgb_pdf.replace('.', '_cmyk.')

    subprocess.run(
        [
            'gs', '-q', '-sDEVICE=pdfwrite',
            '-sColorConversionStrategy=CMYK',
            '-dPDFSETTINGS=/default',
            '-dAutoFilterColorImages=false',
            '-dAutoFilterGrayImages=false',
            '-dColorImageFilter=/FlateEncode',
            '-dGrayImageFilter=/FlateEncode',
            '-dDownsampleMonoImages=false',
            '-dDownsampleGrayImages=false',
            '-dDownsampleColorImages=false',
            '-o', cmyk_pdf, rgb_pdf
        ]
    )

    print(f'CMYK post saved: {cmyk_pdf}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--location_name', type=str,
        help=(
            'Name of location (e.g., house name or number etc).'
            + 'Will be included as is on final poster'
        )
    )
    args = parser.parse_args()

    add_rockwell_font()
    do_plotting(args.location_name)

    rgb_2cmyk(args.location_name)

    # Add scaling percentage here so that text and sig size are appropriate!!!