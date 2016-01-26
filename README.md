# The GTFS Generator

**Table of Contents**


**_My Python Environment Setup_**
Getting started with a [Python Virtual environment on OS X](https://bitbucket.org/Dr_Pete/os-x-virtual-envirionment)
Instructions on setting up a virtual environment using Python on OS X and Jet Brain's 'Pycharm'.

**_gtfsgenerator usage_**
The gtfsgenerator was written for Python version 3.5 and passes configuration and build commands from the command line. For example the command

```
gtfsgenerator -c krt.cfg --generate
```

will generate a GTFS feed using the configuration defined in the file krt.cfg.

## Summary
The gtfsgenerator is designed to assist a transit agency transform existing route information from three data sources.

1. The configuration file is a text file specific to a particular transit agency. The agency and feed info GTFS files
    are written directly from the information in the configuration file. The configuration file is organized into several
    sections.
2. A Google Sheets workbook consisting of worksheets, each worksheet reflecting trip turn-by-turn instructions.
3. Route map line geometry in the form of KML files. KML files can be joined together from KML line segments to create a single shapes.txt file per trip.

### History 
Previous production of general transportation feed specification (GTFS) files for rural West Virginia transit agencies, and the Kanawha Valley Regional Transportation Authority (KRT) located in Charelston, West Virginia in 2012-2013 resulted in a feed file accepted by the Google Transit engineering team and implemented in Google Maps. This effort resulted in enabling riders to use Google Maps with a mobile smart phone/pad or desktop/laptop computer for trip planning.

KRT employed a consulting group to assist in evaluated ways to improve their route and fare structure in 2014. The evaluation led KRT to extensively reworked routes, schedules, and fare structure. The initial GTFS feed relied on several hundred man-hours of translation by graduate students from printed maps and schedules into a master Excel workbook with table that were exported in the comma delimited GTFS format.

Prior Work with developing rural transit agency GTFS workflows focused on the open source TransitDataFeeder. While TransitDataFeeder enabled a shared multi-user data source, a GUI front end, and the ability to process multiple transit agency feeds, TransitDataFeed proved unworkable and difficult to update or maintain, and was abandoned.

A workflow was concieved share the feed construction with  intimate with the routes and schedules might collaborate to produce a more detailed GTFS feed without the burden of special knowledge of GTFS file construction, data management, continued maintenance, or feed verification.

KRT’s ridership audit system provided a path which could be expanded to include the timing details for individual trips while KRT’s route consultants were also exchanging KML files through Google Earth. These two information sources familiar to KRT route planners, provided the leverage to incorporate existing workflows into the development of a complete route, schedule, and geometry maintenance system.

This project expands KRT's ridership audit worksheet and adds route geometry in KML format to produce and verify a complete set of transit agency GTFS files. The workbook and KML parser used to implement GTFS file generation are referred to as the gtfsgenerator.

### Purpose
Previous work at RTI in producing a general transportation feed specification (GTFS) file for the Kanawha Valley Regional Transportation Authority (KRT) in 2012-2013 resulted in a feed that was accepted by the Google Transit engineering team and implemented in Google Maps. This effort resulted in enabling riders to use Google Maps with a mobile smart phone/pad or desktop/laptop computer for trip planning.
After a reevaluation of their route structure in 2014, KRT extensively reworked their routes, schedules, and fares. Rather than repeating the several hundred man-hours in rewriting a new GTFS feed to reflect those changes, RTI suggested that the new GTFS feed development effort provide some shared method by which those most intimate with the routes and schedules might collaborate to produce a more detailed GTFS feed without the burden of special knowledge of GTFS file construction, data management, continued maintenance, or feed verification.
KRT’s ridership audit system provided a path which could be expanded to include the timing details for individual trips while KRT’s route consultants were also exchanging KML files through Google Earth. These two information sources familiar to KRT route planners, provided the leverage to incorporate existing workflows into the development of a complete route, schedule, and geometry maintenance system.
This project integrates an expanded ridership audit worksheet with KML route geometry to produce and verify a complete set of transit agency GTFS files. The workbook and KML parser used to implement GTFS file generation are referred to as the gtfsgenerator.

## GTFS Generator Components
1. Configuration file

    The configuration file is a text file specific to a particular transit agency. The agency, feed_info, and fare,  gtfs files are written directly from the information in the configuration file. The configuration file is organized into several sections.
    * User information
    * Source data locataions
    * GTFS output
    * Agency information
    * GTFS Feed Info
    * Fare information
    * Service holidays

2. Google MyMaps
    * The shapes.txt files are typically constructed from single route line per layer in Google MyMaps.
    * KML layers are exported as single KML files.
    * Multiple line segments can be concatenated in a specified sequence to form a single continuous shapes.txt file.
3. [**_TransitFeed_**](https://github.com/google/transitfeed)
    The feedvalidator.py tool is called by gtfsgenerator to validate the GTFS feed created from each worksheet before combining all trip group feed files into a single GTFS feed file.
***

# The configuration file

### [user] section
The [user] section defines information specific to the user.

- error_path
: Path to error file.
- error_file
: Error file name.

### [source] section
The [source] sections defines where the workbook is located, its name and what row to begin processing.

- source_path
: The source path for the workbook location.
- stops_source_file
: 
- workbook_path
: Path to the Excel workbook used for turn-by-turn instructions.
- workbook_name
: Excel workbook file name.

- row_idx
: Starting entry in Excel workbook. 
- exceptions_path
: Path to an exception file, created when the geocoder does not return a sufficient quality coordinate pair.
- exceptions_file
: The exception file name.

### [gtfs]
The [gtfs] section defines the GTFS output file path, filenames, and distance units used in the feed.

- gtfs_path
: Path to the GTFS format output.
- feed_filename
: File name for the zipped GTFS feed file.
- dist_units
: Valid units are 'miles' or 'kilometers' for determining the distance between stops.

### [agency]
The [agency] section defines the transit agency.txt input values defined by the [GTFS agency.txt](https://developers.google.com/transit/gtfs/reference?hl=en#agencytxt) specification.

- agency_name
- agency_url
- agency_timezone
- agency_id
- agency_lang
- agency_phone
- agency_fare_url

### [feed]
The [feed] section defines the feed_info.txt input values defined by the [GTFS feed_info.txt](https://developers.google.com/transit/gtfs/reference?hl=en#feed_infotxt) specification.

- feed_publisher_name
- feed_publisher_url
- feed_lang
- feed_start_date
- feed_end_date
- feed_version
