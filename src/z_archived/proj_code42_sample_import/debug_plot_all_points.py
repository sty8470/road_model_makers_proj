"""
csv로 된 파일을 읽고, 있는 모든 점 좌표를 plot한다
"""

import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../')))
sys.path.append(current_path + '/../lib/common/')

import numpy as np
import load_csv
import matplotlib.pyplot as plt

# MouseButton.LEFT = 1
# MouseButton.RIGHT = 3

offset_txt_x = 0.5
offset_txt_y = 0.5

def _plot_all(input_path, ax_main, style=None):
    # Change StrDir to Absolute Path
    current_path = os.path.dirname(os.path.realpath(__file__))   

    # inputPath = os.path.normcase(inputPath)
    input_path = os.path.join(current_path, input_path)
    input_path = os.path.normpath(input_path)  

    # read csv
    data = load_csv.read_csv_file(input_path, delimiter=',', names=False)
    print(data.shape)

    x = data[:, 0]
    y = data[:, 1]
    z = data[:, 2]

    if style == None:
        plt.plot(x, y)
    else:
        plt.plot(x, y, style)

    for i in range(len(x)):
        ax_main.text(data[i,0] + offset_txt_x, data[i,1] + offset_txt_y, 'test string')
    # ax_main.text()

    # if style == None:
    #     plt.scatter(x, y)
    # else:
    #     plt.scatter(x, y, style)

    plt.grid(True)

'''NOTE: hjp test code start'''

def onclick(event):
    # test to check onclick functionality
    print('x %d, y %d, xdata %f, ydata %f' %(event.x, event.y, event.xdata, event.ydata))
    # save clicked location
    if event.button == 3:  # MouseButton.RIGHT = 3
        search_coord = [event.xdata, event.ydata]

        # search for nearest node coordinates
        # TODO: figure out how to search within a region, not the entire field

        # draw a circle around the selected node

        # return node information

        # if already node is selected, then deselect the node and erase the circle

def scr_zoom(event):
    # reference https://stackoverflow.com/questions/11551049/matplotlib-plot-zooming-with-scroll-wheel
    # get current axis limits
    ax = event.inaxes
    cur_xlim = ax.get_xlim()
    cur_ylim = ax.get_ylim()
    cur_xrange = (cur_xlim[1] - cur_xlim[0])*0.5
    cur_yrange = (cur_ylim[1] - cur_xlim[0])*0.5

    # recognize scroll event
    if event.button == 'up':
        #zoom in
        sf = 0.5
    elif event.button == 'down':
        #zoom out
        sf = 2
    else:
        # error
        raise Exception('Scroll error')

    # set new axis limits
    # ax.set_xlim([event.xdata - cur_xrange*sf, event.xdata + cur_xrange*sf])
    # ax.set_ylim([event.ydata - cur_yrange*sf, event.ydata + cur_yrange*sf])
    ax.set_xlim([event.xdata - (event.xdata - cur_xlim[0])*sf, event.xdata + (cur_xlim[1] - event.xdata)*sf])
    ax.set_ylim([event.ydata - (event.ydata - cur_ylim[0])*sf, event.ydata + (cur_ylim[1] - event.ydata)*sf])

    # redraw plot
    plt.draw()

'''NOTE: hjp test code end'''

def main():
    print('[INFO] main starts')

    # input_path = '../../output/geojson_code42/toGwacheonSample/output_CROSSWALK.csv'
    # input_path = '../../output/geojson_code42/toGwacheonSample/output_SPEEDBUMP.csv'
    
    fig = plt.figure()
    ax_main = plt.subplot(111)

    # call the function for it
    input_path = '../../output/geojson_code42/toGwacheonSample/Lane_Border.csv'
    _plot_all(input_path, 'b.')

    # call the function for it
    input_path = '../../output/geojson_code42/toGwacheonSample/Lane_Center.csv'
    _plot_all(input_path, 'r.')

    # # call the function for it
    # input_path = '../../output/geojson_code42/toGwacheonSample/Lane_Border_WSS.csv'
    # _plot_all(input_path, '-k.')

    # input_path = '../../output/geojson_code42/toGwacheonSample/Lane_Border_YDS.csv'
    # _plot_all(input_path, '-k.')

    # input_path = '../../output/geojson_code42/toGwacheonSample/Lane_Border_YSS.csv'
    # _plot_all(input_path, '-k.')

    ''' NOTE: hjp test code start'''
    cid_click = fig.canvas.mpl_connect('button_press_event', onclick)
    cid_scroll = fig.canvas.mpl_connect('scroll_event', scr_zoom)
    ''' NOTE: hjp test code end'''

    plt.show()
    print('[INFO] main ended')

if __name__ == u'__main__':
    main()