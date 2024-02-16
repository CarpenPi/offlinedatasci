#Creating directory for R files if it does not exist
# Download files using download files.py
#Downloading Data Carpentry website using httrack

from pathlib import Path
import airium
import bs4 as bs
import os
import re
import subprocess
import urllib.request, urllib.error, urllib.parse
import importlib_resources
import pypi_mirror
import shutil
import sys
import warnings

def add_lesson_index_page(lesson_path):
    """Add a basic landing page for lessons
    
    Uses the top-level directory name to group lessons into sections by source
    Then displays an unordered list of lessons within each source

    """
    lesson_path = Path(lesson_path)
    a = airium.Airium()
    a('<!DOCTYPE html>')
    sources = next(os.walk(lesson_path))[1]
    with a.html():
        for source in sources:
            with a.head():
                a.meta(charset="utf-8")
                a.title(_t="Lessons")
            with a.body():
                a.h1(_t="Lesson Material")
                a.h2(_t=source.replace('-', ' ').title())
            lessons = next(os.walk(Path(lesson_path, Path(source))))[1]
            with a.ul():
                for lesson in lessons:
                    with a.li():
                        lesson_index = Path(Path(source), Path(lesson), Path("index.html"))
                        with a.a(href = lesson_index):
                            a(lesson.replace('-', ' ').title())

    with open(Path(Path(lesson_path), Path("index.html")), "w+") as index_file:
        index_file.writelines(str(a))

def activate(ods_dir):
    """Use local mirrors for CRAN and PyPI repositories

    Parameters:
    ods_dir (str): The directory where the offline data science (ods) environment is located. 
                   This directory should contain the miniCRAN and PyPI repositories.

    Modifies the .Rprofile and pip.conf files in the user's home directory to set the CRAN and PyPI 
    repositories to the local mirrors located in the ods_dir.

    The function does not return any value. It modifies the .Rprofile and pip.conf files in place.
    """
        
    activate_cran(ods_dir)
    activate_pypi(ods_dir)

def activate_cran(ods_dir):
    """Use local mirror of CRAN

    Parameters:
    ods_dir (str): The directory where the offline data science (ods) environment is located. 
                   This directory should contain the miniCRAN repository.

    The function works by adding a line to the .Rprofile file that sets the CRAN repository to the miniCRAN repository 
    located in the ods_dir. If this line already exists in the .Rprofile file, it is not added again. If the line exists 
    but is commented out, it is uncommented.

    The function does not return any value. It modifies the .Rprofile file in place.
    """

    minicran_path = os.path.join("file://", ods_dir.lstrip("/"), "miniCRAN") #lstrip needed because "If any component is an absolute path, all previous path components will be discarded"
    rprofile_line = 'local({r <- getOption("repos"); r["CRAN"] <- "%s"; options(repos=r)}) #Added by offlinedatasci\n' % minicran_path
    rprofile_path = Path(os.path.join(os.path.expanduser("~"), ".Rprofile"))
    if rprofile_path.is_file():
        with open(rprofile_path) as input:
            rprofile_list = list(input)
    else:
        rprofile_list = []
    with open(rprofile_path, 'w') as output:
        activated = False
        for line in rprofile_list:
            if line.strip() == rprofile_line.strip():
                output.write(line)
                activated = True
            elif line.strip() == f"#{rprofile_line.strip()}":
                output.write(rprofile_line)
                activated = True
            else:
                output.write(line)
        if not activated:
            output.write(rprofile_line)

def activate_pypi(ods_dir):
    """Use local mirror of PyPI

    Parameters:
    ods_dir (str): The directory where the offline data science (ods) environment is located. 
                   This directory should contain the PyPI repository in a pypi subdirectory.

    The function works by adding a line to the ~/.config/pip.conf file that sets the index-url to the PyPI repository 
    located in the ods_dir. If this line already exists in the pip.conf file, it is not added again. If the line is
    commented out, it is uncommented.

    The function does not return any value. It modifies the pip.conf file in place.
    """

    pypi_path = os.path.join("file:///", ods_dir.lstrip("/"), "pypi") #lstrip needed because "If any component is an absolute path, all previous path components will be discarded"
    pip_config_line = f"#Added by offlinedatasci\n[global]\nindex-url = {pypi_path}\n"
    pip_config_folder_path = Path(os.path.join(os.path.expanduser("~"), ".config", "pip"))
    pip_config_path = Path(pip_config_folder_path, "pip.conf")
    if not pip_config_folder_path.is_dir():
        print("\nCreating .config/pip folder in home directory")
        Path.mkdir(pip_config_folder_path, parents=True)
    if pip_config_path.is_file():
        with open(pip_config_path) as input:
            pip_config_list = list(input)
    else:
        pip_config_list = []
    with open(pip_config_path, 'w') as output:
        if not pip_config_list:
            output.write(pip_config_line)
        else:
            activated = False
            for line in pip_config_list:
                if line.strip() == pip_config_line.strip():
                    output.write(line)
                    activated = True
                elif line.strip() == f"#{pip_config_line.strip()}":
                    output.write(pip_config_line)
                    activated = True
                else:
                    output.write(line)
            if not activated:
                output.write(pip_config_line)
    
def deactivate():
    """Stop using the local CRAN and PyPI mirrors
    
    Removes any lines added by offlinedatasci to ~/.Rprofile and ~/.config/pip/pip.conf
    """
    deactivate_cran()
    deactivate_pypi()

def deactivate_cran():
    """Stop using the local CRAN mirror

    Removes any lines added by offlinedatasci to ~/.Rprofile 
    """
    rprofile_path = os.path.join(os.path.expanduser("~"), ".Rprofile")
    with open(rprofile_path) as input:
        rprofile_list = list(input)
    with open(rprofile_path, 'w') as output:
        for line in rprofile_list:
            if "#Added by offlinedatasci" in line.strip():
                pass
            else:
                output.write(line)

def deactivate_pypi():
    """Stop using the local PyPI mirror

    Removes any lines added by offlinedatasci to ~/.config/pip/pip.conf 
    """
    pip_config_folder_path = Path(os.path.join(os.path.expanduser("~"), ".config", "pip"))
    pip_config_path = Path(pip_config_folder_path, "pip.conf")
    with open(pip_config_path) as input:
        pip_config_list = list(input)
    last_line_ods_comment = False
    next_last_line_ods_comment = False
    with open(pip_config_path, 'w') as output:
        for line in pip_config_list:
            if "#Added by offlinedatasci" in line.strip():
                last_line_ods_comment = True
            elif last_line_ods_comment:
                next_last_line_ods_comment = True
                last_line_ods_comment = False
            elif next_last_line_ods_comment:
                next_last_line_ods_comment = False
            else:
                output.write(line)

def download_and_save_installer(latest_version_url, destination_path):
    """Download and save installer in user given path.

    Keyword arguments:
    latest_version_url -- Link to download installer
    destination_path -- Path to save installer
    """
    if not os.path.exists(destination_path):
                print("****Downloading file: ", destination_path)    
                urllib.request.urlretrieve(latest_version_url, destination_path) 
    else:
        print("File not being downloaded")


def download_r(ods_dir):
    """Download most recent version of R installer (mac and windows) from CRAN

    Keyword arguments:
    destination_path -- Path to save installers
    """
    destination_path = Path(Path(ods_dir), Path("R"))
    if not os.path.isdir(destination_path):
        os.makedirs(destination_path)

    latest_version_url = "https://cloud.r-project.org/bin/macosx/"
    r_current_version = find_r_current_version(latest_version_url)
    download_r_windows(r_current_version, ods_dir)
    download_r_macosx(r_current_version, ods_dir)


def download_lessons(ods_dir):
    """Downloads the workshop lessons as rendered HTML.
    Keyword arguments:
    destination_path -- Path to save rendered HTML lessons
    """

    if not shutil.which('wget'):
        warnings.warn("""wget not detected so not downloading lessons.

        wget needs to be installed on your computer to clone lesson websites.

        macOS: you can install wget using Xcode command line tools
               or using `conda install wget -c conda-forge` if you are using conda.
        
        Windows: you can download a wget binary from: https://eternallybored.org/misc/wget/
        """)
        return

    dc_lessons = ["https://datacarpentry.org/ecology-workshop/",
                  "https://datacarpentry.org/spreadsheet-ecology-lesson/",
                  "http://datacarpentry.org/OpenRefine-ecology-lesson/",
                  "https://datacarpentry.org/R-ecology-lesson/",
                  "https://datacarpentry.org/python-ecology-lesson/",
                  "https://datacarpentry.org/sql-ecology-lesson/"]
    lc_lessons = ["https://librarycarpentry.org/lc-overview/",
                  "https://librarycarpentry.org/lc-data-intro/",
                  "https://librarycarpentry.org/lc-shell/",
                  "https://librarycarpentry.org/lc-open-refine/",
                  "https://librarycarpentry.org/lc-git/",
                  ]

    lesson_path = Path(Path(ods_dir), Path("lessons"))
    if not os.path.isdir(lesson_path):
        os.makedirs(lesson_path)

    for lesson in dc_lessons:
        print(f"Downloading lesson from {lesson}")
        subprocess.run(["wget", "-r", "-k", "-N", "-c", "--no-parent", "--no-host-directories",
                        "-P", Path(lesson_path, "data-carpentry"), lesson],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT)
        
    for lesson in lc_lessons:
        print(f"Downloading lesson from {lesson}")
        subprocess.run(["wget", "-r", "-k", "-N", "-c", "--no-parent", "--no-host-directories",
                        "-P", Path(lesson_path, "library-carpentry"), lesson],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.STDOUT)

    sc_lessons = ["http://swcarpentry.github.io/shell-novice",
                  "http://swcarpentry.github.io/git-novice",
                  "http://swcarpentry.github.io/python-novice-inflammation",
                  "http://swcarpentry.github.io/python-novice-gapminder",
                  "http://swcarpentry.github.io/r-novice-inflammation",
                  "http://swcarpentry.github.io/r-novice-gapminder",
                  "http://swcarpentry.github.io/shell-novice-es",
                  "http://swcarpentry.github.io/git-novice-es",
                  "http://swcarpentry.github.io/r-novice-gapminder-es"]

    # Software Carpentry lessons have external CSS so requires a more expansive search & rewriting to get all necessary files
    for lesson in sc_lessons:
        print(f"Downloading lesson from {lesson}")
        subprocess.run(["wget", "-p", "-r", "-k", "-N", "-c", "-E", "-H", "-D",
                        "swcarpentry.github.io", "-K", "--no-parent", "--no-host-directories",
                        "-P", Path(lesson_path, "software-carpentry"), lesson],
                       stdout = subprocess.DEVNULL,
                       stderr = subprocess.STDOUT)
        
    add_lesson_index_page(lesson_path)

def download_rstudio(ods_dir):
    """Download RStudio installers"""
    baseurl = 'https://www.rstudio.com/products/rstudio/download/#download'
    destination_path = Path(Path(ods_dir), Path("rstudio"))
    if not os.path.isdir(destination_path):
        os.makedirs(destination_path)
    fp = urllib.request.urlopen(baseurl)
    web_content = fp.read()
    soup = bs.BeautifulSoup(web_content, 'lxml')
    links = soup.find_all('a')
    for link in links:
        if link.has_attr('href') and (".exe" in link['href'] or ".dmg" in link['href']):
            url = str(link['href'])
            download_and_save_installer(url, Path(Path(destination_path), Path(os.path.basename(url))))

def download_python(ods_dir):
    """Download Python installers from HTML page

    Keyword arguments:
    ods_dir -- Directory to save installers
    """
    url = get_python_download_page()
    download_table_num=0
    oscolnum=1
    hrefcolnum=0
    key="version"

    destination_path = Path(Path(ods_dir), Path("python"))
    if not os.path.isdir(destination_path):
        os.makedirs(destination_path)
    python_versions = {}
    fp = urllib.request.urlopen(url)
    web_content = fp.read()
    soup = bs.BeautifulSoup(web_content, 'lxml')
    r_studio_download_table = soup.find_all('table')[download_table_num]
    table_body = r_studio_download_table.find('tbody')
    python_versions = {}
    for row in table_body.find_all("tr"):
      os_data = table_parse_version_info(row,oscolnum,hrefcolnum)
      os_version = os_data[key] 
      python_versions[os_version] = os_data
    for key in python_versions.keys():
        is_windows = "embeddable" not in key and "help" not in key and key.startswith("Windows")
        is_macos = key.startswith("macOS")
        if (is_macos or is_windows):
          download_link = python_versions[key]["url"]
          destination_path2 = Path(Path(destination_path), Path(os.path.basename(download_link)))
          download_and_save_installer(download_link, destination_path2)

def find_r_current_version(url):
    """Determine the most recent version of R from CRAN

    Keyword arguments:
    url -- CRAN r-project URL
    """
    version_regex = "(R\-\d+\.\d+\.\d)+\-(?:x86_64|arm64|win)\.(?:exe|pkg)"
    urlfile = urllib.request.urlopen(url)
    for line in urlfile:
        decoded = line.decode("utf-8") 
        match = re.findall(version_regex, decoded)
        if (match):
            r_current_version = match[0].strip(".exe").strip(".pkg")
            return r_current_version
    return None

def download_r_windows(r_current_version, ods_dir):
    """Download the most recent version of R installer for Windows from CRAN.

    Keyword arguments:
    r_current_version -- The most recent version of R
    ods_dir -- Directory to save R installers
    """
    baseurl = "https://cloud.r-project.org/bin/windows/base/"
    download_path = baseurl + r_current_version + "-win.exe"
    destination_path = Path(Path(ods_dir), Path("R"), Path(r_current_version + "-win.exe"))
    if not os.path.exists(destination_path):
        print("****Downloading file: ", destination_path)
        urllib.request.urlretrieve(download_path, destination_path)

def download_r_macosx(r_current_version, ods_dir):
    """Download the most recent version of R installer for MacOSX from CRAN.

    Keyword arguments:
    r_current_version -- The most recent version of R
    ods_dir -- Directory to save R installers
    """
    baseurl = "https://cloud.r-project.org/bin/macosx/"
    download_path_arm64 = baseurl + "big-sur-arm64/base/" + r_current_version + "-arm64.pkg"
    destination_path_arm64 = Path(Path(ods_dir), Path("R"), Path(r_current_version + "-arm64.pkg"))
    if not os.path.exists(destination_path_arm64):
        print("****Downloading file: ", destination_path_arm64)
        urllib.request.urlretrieve(download_path_arm64, destination_path_arm64)

    download_path_x86_64 = baseurl + "big-sur-x86_64/base/" + r_current_version + "-x86_64.pkg"
    destination_path_x86_64 = Path(Path(ods_dir), Path("R"), Path(r_current_version + "-x86_64.pkg"))
    if not os.path.exists(destination_path_x86_64):
        print("****Downloading file: ", destination_path_x86_64)
        urllib.request.urlretrieve(download_path_x86_64, destination_path_x86_64)

def get_ods_dir(directory=Path.home()):
    """Get path to save downloads, create if it does not exist.

    Keyword arguments:
    directory -- Path to save downloads (defaults to user home path)
    """
    folder_path = Path(directory)
    if not folder_path.is_dir():
        print("\nCreating ods folder in " + str(directory))
        Path.mkdir(folder_path, parents=True)
    return str(folder_path)

def get_python_download_page():
    """Get download page from Python homepage."""
    base_url="https://www.python.org"
    fp = urllib.request.urlopen(base_url)
    web_content = fp.read()
    soup = bs.BeautifulSoup(web_content, "html.parser")
    release_a_tag = soup.find("a", href=lambda href: href and "release" in href)
    current_release_path = release_a_tag["href"]
    current_release_url = base_url + current_release_path
    return(current_release_url)

def table_parse_version_info(row,oscolnum,hrefcolnum):
    """Parse and return software information from table.

    Keyword arguments:
    row -- Row from HTML table
    oscolnum -- Number of column in which OS is found
    hrefcolnum -- Number of column in which HREFs are found
    """
    # OS / LINK / SIZE / SHA-256
    columns = row.find_all("td") # find all columns in row
    os = columns[oscolnum].text.strip() # return first column data (OS)
    link = columns[hrefcolnum].a # return second column data (href) and access atag with href
    link_url = link['href'].strip()
    link_inner_html = link.text.strip()
    return {"osver": os, "version": link_inner_html, "url": link_url}        

def download_minicran(ods_dir,
                      py_library_reqs = ["tidyverse", "RSQLite"],
                      r_version = None):
    """Creating partial CRAN mirror of workshop libraries.

    Keyword arguments:
    ods_dir -- Directory to create CRAN mirror
    """
    if not shutil.which('Rscript'):
        warnings.warn("""Rscript not detected so not installing miniCRAN.

        R needs to be installed on your computer to clone lesson websites.

        Install R from: https://cloud.r-project.org/
        """)
        return
    
    if r_version is None:
        r_version = find_r_current_version("https://cloud.r-project.org/bin/windows/base/")
    
    r_major_minor_version_nums = r_version.replace('R-', '').split('.')
    r_major_minor_version = '.'.join(r_major_minor_version_nums[:2])

    minicranpath = importlib_resources.files("offlinedatasci") / "miniCran.R"
    custom_library_string = ' '.join(py_library_reqs)
    subprocess.run(["Rscript", minicranpath, ods_dir, custom_library_string, r_major_minor_version])


def download_python_libraries(ods_dir,py_library_reqs = [ "matplotlib", "notebook","numpy", "pandas"] ):
    """Creating partial PyPI mirror of workshop libraries.

    Keyword arguments:
    ods_dir -- Directory to save partial Pypi mirror
    """
    #workshop_needed_libraries = pandas, matplotlib, numpy
    #python_included_libraries = math, random, glob, time, sys, pathlib
    download_dir = Path(Path(ods_dir), Path("pythonlibraries"))
    pypi_dir = Path(Path(ods_dir), Path("pypi"))
    parameters = {
        'pip': 'pip3',
        'dest': download_dir,
        'pkgs': py_library_reqs,
        'python_version': '3.11',
        'allow_binary': True
    }
    pypi_mirror.download(platform = ['manylinux_2_17_x86_64'], **parameters)
    pypi_mirror.download(platform = ['macosx_10_12_x86_64'], **parameters)
    pypi_mirror.download(platform = ['win_amd64'], **parameters)
    mirror_creation_parameters = {
        'download_dir': download_dir,
        'mirror_dir': pypi_dir,
        'copy': True
    }
    pypi_mirror.create_mirror(**mirror_creation_parameters)

def get_default_packages(language):
    packages = { 
        "r": {
            "data-carpentry": ["tidyverse", "RSQLite"],
            "data-science": ["dplyr", "ggplot2", "shiny", "lubridate", "knitr",
                             "esquisse", "mlr3", "knitr", "DT", "ratdat"]
        },
        "python": {
            "data-carpentry": ["pandas", "notebook", "numpy", "matplotlib", "plotnine"], 
            "software-carpentry": ["matplotlib", "notebook", "numpy", "pandas"] ,
            "data-science": ["scipy", "numpy", "pandas", "matplotlib", "keras", "scikit-learn", "beautifulsoup4", "seaborn","torch"]
        }
    }
    return packages[language]


def package_selection(language, custom_package_list):
    language_dictionary = get_default_packages(language)
    packages_to_download = []
    for item in custom_package_list:
        if item in [*language_dictionary]:
            packages_to_download.extend(language_dictionary[item])
        else:
            packages_to_download.append(item)
    packages_to_download = list(set(packages_to_download))
    return packages_to_download

def try_except_functions(input,functions):
    if not isinstance(functions, list):
        functions = [functions]
    for function in functions:
        try:
            function(input)
        except Exception as e:
            print( f"Error in function: {function.__name__}. Error: {str(e)}")