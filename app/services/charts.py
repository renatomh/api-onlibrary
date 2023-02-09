# -*- coding: utf-8 -*-

# Module to get the environment variables
import os

# Getting the required variables
from config import OUTPUT_FOLDER

# Libraries for charts creation
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.stats import norm, iqr

# Treemap algorithm library
import squarify

# Defining a default color set
default_colors = [
    "#f94144", # Red Salsa
    "#277da1", # CG Blue
    "#43aa8b", # Zomp
    "#f3722c", # Orange Red
    "#f8961e", # Yellow Orange Color Wheel
    "#f9844a", # Mango Tango
    "#f9c74f", # Maize Crayola
    "#90be6d", # Pistachio
    "#4d908e", # Cadet Blue
    "#577590", # Queen Blue
]

# Function to generate pie charts
def get_pie_chart(dataset=None, filename='pie_chart', plttype=3, colors=default_colors):
    # The dataset must be passed as a dict with labels and values lists, like so
    dataset = {
        'labels': ['Group A', 'Group B', 'Group C', 'Group D'],
        'values': [12, 11, 3, 30],
    } if dataset is None else dataset
    
    try:
        # Defining the plotting type (value and percentage, only percentage or only value)
        plttype_dict = {
            # Percentage and value
            1: (lambda p: '{:.2f}% ({:.0f})'.format(p, (p/100) * sum(dataset['values']))),
            # Only percentage
            2: (lambda p: '{:.2f}%'.format(p)),
            # Only value
            3: (lambda p: '{:.0f}'.format((p/100) * sum(dataset['values']))),
        }
    
        # Creating the chart
        plt.pie(
            # Defining values
            dataset['values'],
            # Defining labels
            labels=(dataset['labels']),
            # Defining colors
            colors=colors,
            autopct=plttype_dict[plttype],
            pctdistance=0.8,
            # Other chart properties
            wedgeprops={'linewidth' : 1, 'edgecolor': 'white'},
            labeldistance=1.25,
            textprops={'fontsize': 'small', 'fontfamily': 'sans-serif'},
        )
        
        # Saving image and returning the filename
        # Must be called before 'plt.show()', since this function would open a new 'canvas'
        plt.savefig(OUTPUT_FOLDER + os.sep + filename + '.png', bbox_inches='tight', dpi=200, transparent=True)
        #plt.show()
        plt.close()

        # Returning the generated plot path
        return (OUTPUT_FOLDER + os.sep + filename + '.png')

    # If something goes wrong
    except Exception as e:
        print(e)
        plt.close()
        return None

# Function to generate treemap
def get_treemap(dataset=None, filename='treemap', colors=default_colors):
    # The dataset must be passed as a dict with labels and values lists, like so
    dataset = {
        'labels': ['Group A', 'Group B', 'Group C', 'Group D'],
        'values': [12, 11, 3, 30],
    } if dataset is None else dataset
    
    try:
        # Creating the dataframe
        df = pd.DataFrame({'values': dataset['values'], 'labels': dataset['labels']})
        # Sorting by the values
        df = df.sort_values('values', ascending=False)
        
        # Generating the treemap chart
        squarify.plot(
            # Area sizes
            sizes=df['values'],
            # Values and labels
            value=df['values'],
            label=df['labels'],
            # Alpha channel (transparency)
            alpha=0.8,
            # Areas colors
            color=colors,
            # X and Y axis normalization (area distribution)
            norm_x=50,
            norm_y=75,
        )
        
        # Removing axis for better visualization
        plt.axis('off')
        
        # Saving image and returning the filename
        # Must be called before 'plt.show()', since this function would open a new 'canvas'
        plt.savefig(OUTPUT_FOLDER + os.sep + filename + '.png', bbox_inches='tight', dpi=200, transparent=True)
        #plt.show()
        plt.close()
        return (OUTPUT_FOLDER + os.sep + filename + '.png')
    
    # If something goes wrong
    except Exception as e:
        print(e)
        plt.close()
        return None

# Function to generate horizontal bar plot
def get_barh_plot(dataset=None, filename='barh_plot', ylbltype=1, colors=default_colors):
    # The dataset must be passed as a dict with labels and values lists, like so
    dataset = {
        'labels': ['Group A', 'Group B', 'Group C', 'Group D'],
        'values': [12, 11, 3, 30],
    } if dataset is None else dataset

    try:
        # Creating the dataframe
        df = pd.DataFrame({'values': dataset['values'], 'labels': dataset['labels']})
        # Sorting by the values
        df = df.sort_values('values', ascending=True)
        
        # Defining the y-label type (group labels or indexes)
        y_label = {
            # Groups
            1: df['labels'],
            # Group indexes
            2: [str(idx) for idx in range(len(df['labels']), 0, -1)],
        }
        
        # Generating the horizontal bar plot
        h = plt.barh(
            # Y label
            y=y_label[ylbltype],
            # Size (values)
            width=df['values'],
            # Bars height
            height=0.8,
            # Alpha channel (transparency)
            alpha=0.6,
            # Chart colors
            color=colors,
        )
        
        # Inserting values on the bars
        for idx, value in enumerate(df['values']):
            # Adding the lable
            plt.text(
                # X and Y position (centered)
                value-(value/2), idx,
                # Value to be presented
                str(value),
                # Label color and font weight
                color='white', fontweight='bold'
                )
        
        # Adding the legend to the chart
        plt.legend(h, df['labels'], loc=[0.7,0.1])
        
        # Saving image and returning the filename
        # Must be called before 'plt.show()', since this function would open a new 'canvas'
        plt.savefig(OUTPUT_FOLDER + os.sep + filename + '.png', bbox_inches='tight', dpi=200, transparent=True)
        #plt.show()
        plt.close()
        return (OUTPUT_FOLDER + os.sep + filename + '.png')

    # If something goes wrong
    except Exception as e:
        print(e)
        plt.close()
        return None

# Function to insert values on bar plot bars
def autolabel(ax, rects):
    # For each bar in set plot
    for rect in rects:
        # Getting the bar height
        height = rect.get_height()
        # Defining axis text
        ax.text(
            # Setting X position for label
            rect.get_x() + rect.get_width()/2.,
            # Setting Y position (height) for label
            #1.05*height,
            height/3,
            # Formatting value to be presented
            '%d' % int(height),
            # Defining horizontal and vertical alignment
            ha='center', va='bottom')

# Function to generate bar plot
def get_bar_plot(dataset=None, filename='bar_plot', colors=default_colors):
    # Dataset must be formatted like the example below
    dataset = {
        'labels': ['Value 1', 'Value 2', 'Value 3'],
        'Value 1': [30, 22, 18, 16, 15],
        'Value 2': [12, 11, 9, 8, 8],
        'Value 3': [9, 8, 2, 2, 1],
        'ticks': ['Group A', 'Group B', 'Group C', 'Group D', 'Group E'],
        'ylabel': 'Group values (un)',
        'title': 'Plot Title',
    } if dataset is None else dataset

    try:
        # Defining samples number (from first group)
        n = len(dataset[dataset['labels'][0]])
        
        # Defining X locations for the groups
        ind = np.arange(n)
        # Defining bar widths
        width = 1/len(dataset['labels']) - 0.05
        
        # Creating the subplots
        fig, ax = plt.subplots()
        
        # Defining the bars for the groups
        rects = []
        for idx, label in enumerate(dataset['labels']):
            rects.append(
                ax.bar(
                    # Groups and sizes (values)
                    x=ind+width*idx,
                    height=dataset[label],
                    # Bar widths and transparency (alpha channel)
                    width=width, alpha=0.8,
                    # Plot colors and legend
                    color=colors[idx]
                )
            )
        
        # Adding text for legends, titles and axis
        if 'ylabel' in dataset: ax.set_ylabel(dataset['ylabel'])
        if 'title' in dataset: ax.set_title(dataset['title'])
        ax.set_xticks(ind + width / 2)
        ax.set_xticklabels(dataset['ticks'])
        
        # Getting list with all values
        all_values_set = set(
            [item for sublist in
                [l for l in
                    [dataset[label] for label in dataset['labels']]
                ] for item in sublist
            ]
        )
        
        # Defining axis limits
        #ylim_inf = min(all_values_set)
        ylim_inf = 0
        ylim_sup = max(all_values_set)
        ax.set_ylim([ylim_inf, ylim_sup])
        
        # Inserting legend
        ax.legend(rects, dataset['labels'])
        
        # Inserting values labels on bars
        for rect in rects:
            autolabel(ax, rect)
        
        # Saving image and returning the filename
        # Must be called before 'plt.show()', since this function would open a new 'canvas'
        plt.savefig(OUTPUT_FOLDER + os.sep + filename + '.png', bbox_inches='tight', dpi=200, transparent=True)
        #plt.show()
        plt.close()
        return (OUTPUT_FOLDER + os.sep + filename + '.png')

    # If something goes wrong
    except Exception as e:
        print(e)
        plt.close()
        return None

# Function to generate histogram plot
def get_histogram_plot(dataset=None, filename='histogram_plot', density=False, num_bins=None, 
    colors=default_colors):
    # Dataset must be formatted like the example below
    dataset = {
        'values': np.random.randint(low=1, high=100, size=1500),
        'xlabel': 'Intervalos',
        'ylabel': 'Distribuição das Frequências',
        'title': 'Histograma dos Valores',
    } if dataset is None else dataset
    
    try:
        # Defining number of bins number to be presented (if none set)
        if num_bins is None:
            num_bins = round((max(dataset['values']) - min(dataset['values']))/
                            (2*(iqr(dataset['values'])/(len(dataset['values'])**(1/3)))))
        
        # Creating the subplots
        fig, ax = plt.subplots()
        
        # Creating histogram with values set
        n, bins, patches = ax.hist(
            # Data set and number of bins
            x=dataset['values'], bins=num_bins,
            # Setting plot for density or frequency
            density=density,
            # Data labels
            label=dataset['ylabel'] if 'ylabel' in dataset else 'Frequency',
            # Other options
            color=colors[0],
            edgecolor='white',
        )
        
        # Getting the distribution mean and standard deviation
        (mu, sigma) = norm.fit(dataset['values'])
        
        # Adding lien with dataset mean value
        plt.axvline(x=mu, color='black', linestyle='dashed', linewidth=1)
        # Adding mean value line label
        min_ylim, max_ylim = plt.ylim()
        plt.text(mu*1.05, max_ylim*0.9, 'Média: {:.2f}'.format(mu))
        
        # If we are using density
        if density:
            # Adding a better regression line
            y = ((1/(np.sqrt(2*np.pi) * sigma)) * np.exp(-0.5*(1/sigma * (bins-mu))**2))
            ax.plot(bins, y, '--')
            # Defining the label formatting
            anot_format = '{:.4f}'
        
        # If we are using absolute values
        else: anot_format = '{:.0f}'
        
        # Setting X coordinates for labels
        bin_centers = np.diff(bins)*0.5 + bins[:-1]
        
        # Inserting labels on bins
        for idx, x in enumerate(bin_centers):
            # Defining label text
            height = n[idx]
            plt.annotate(
                # Value to be show
                anot_format.format(height),
                # Upper left on histogram bin
                xy = (x, height),
                # Label offest above bin
                xytext = (0,0.2),
                # 'xy' value offest in points
                textcoords = "offset points",
                # Horizontal e vertical alignment
                ha = 'center', va = 'bottom'
            )
        
        # Adding labels and title
        if 'xlabel' in dataset: ax.set_xlabel(dataset['xlabel'])
        if 'ylabel' in dataset: ax.set_ylabel(dataset['ylabel'])
        if 'title' in dataset: ax.set_title(dataset['title'])
        
        # Adjusting spacing to avoid Y axis cutting
        fig.tight_layout()
        
        # Inserting legend
        plt.legend()
        
        # Saving image and returning the filename
        # Must be called before 'plt.show()', since this function would open a new 'canvas'
        plt.savefig(OUTPUT_FOLDER + os.sep + filename + '.png', bbox_inches='tight', dpi=200, transparent=True)
        #plt.show()
        plt.close()
        return (OUTPUT_FOLDER + os.sep + filename + '.png')

    # If something goes wrong
    except Exception as e:
        print(e)
        plt.close()
        return None
