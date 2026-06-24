QGIS_TOC_GROUPS = ['Raw_Data', 'Reprojected_Data', 'Sampling', 'Kriging', 'Validation', 'Error_Compensation',
                   'Gain_Surface']

DIRECTORY_STRUCTURE = {'00_Data': ['00_Raw_Files', '01_Reproject', '02_Sampling'],
                       '01_Kriging': ['01_T1_T2_Total', '02_T1_Total', '03_T2_Total', '04_T1_80perc', '05_T2_80perc'],
                       '02_Validation': [],
                       '03_Error_Compensation': ['T1_Error_Compensation', 'T2_Error_Compensation'],
                       '04_Gain_Surface': [],
                       '05_Results': ['01_Histograms', '02_Variograms', '03_Maps']}

POLYGONS_BUILDER_METHODS = ['Boucle rang', 'Ligne parcelle']
FILTERING_TARGET_PROJECTION = ['Lambert93', 'UTM']
FILTERING_COLONNE_DATE = ['Yes', 'No']
SAMPLING_LAYER_NAMES = ['T1_total', 'T1_80_perc', 'T1_20_perc', 'T2_total', 'T2_80_perc', 'T2_20_perc']

DEFAULT_SETTINGS = {
    'SERVER': ['BD_GEOSTAT_LPC', 'localhost', '5432', 'postgres', 'postgres'],
    'TREATMENT': [False, True, 'T1', 'T2', 10.0, 0.0, 1.0],
    'KRIGING': ['VRYIELDMAS;VRYIELD', 1.5, 1.5],
    'HISTOGRAM': [30, '#636efa', '#000000'],
    'SYMBOLOGY': [4, '#bfbcbc', '#ffff00', '#55ff00', '#267300']
}

STATISTICS_INTERVAL = {'DATA': [], 'YIELD_SUM': float, 'SQ_AREA': float, 'PERC_AREA': float,
                       'YIELD_BY_PERC_AREA': float}

STATISTICS_INTERVALS = {
    'FIRST_INTERVAL': {'DATA': [], 'SQ_AREA': float, 'PERC_AREA': float, 'YIELD_BY_PERC_AREA': float},
    'SECOND_INTERVAL': {'DATA': [], 'SQ_AREA': float, 'PERC_AREA': float, 'YIELD_BY_PERC_AREA': float},
    'THIRD_INTERVAL': {'DATA': [], 'SQ_AREA': float, 'PERC_AREA': float, 'YIELD_BY_PERC_AREA': float},
    'FOURTH_INTERVAL': {'DATA': [], 'SQ_AREA': float, 'PERC_AREA': float, 'YIELD_BY_PERC_AREA': float},
}

GAIN_SURFACE_DATA = {
    'SUM': float,
    'MEAN': float,
    'MODE': float,
    'MEDIAN': float,
    'STD_DEV': float,
    'ANOVA': [],
    'INTERVALS': STATISTICS_INTERVALS,
    'TOTAL_AREA': float,
    'TOTAL_YIELD_PRODUCTION': float,
}

CROP_COLUMN_NAMES = ['Id', "Crop name", "Sowing date", "Harvesting date", "Variety", "InterRoCM", "Create date",
                     "Update date"]
FARMER_COLUMN_NAMES = ['Id', "First name", "Last name", "Address", "Zipcode", "Town", "Country", "Create date",
                       "Update date"]
GEOSTATISTIC_TRIAL = ['Id', "Field name", "Area", "Irrigated", "Soil type", "LPC Team", "Farmer", "Crop field",
                      "Contour",
                      "Create date", "Update date"]

FETCH_ALL_DOMAIN = "SELECT * FROM yes_or_not_domain;"



FETCH_ALL_CROP = "SELECT * FROM crop_trial;"
FETCH_ONE_CROP = "SELECT * FROM crop_trial WHERE id = '{}';"

FETCH_ALL_FARMER = "SELECT * FROM farmer;"
FETCH_ONE_FARMER = "SELECT * FROM farmer WHERE id = '{}';"



INSERT_CROP_SQL = "INSERT INTO crop_trial (crop_name, sowing_date, harvest_date, variety, inter_ro_cm, " \
                  "create_date) VALUES (?, ?, ?, ?, ?, ?);"
UPDATE_CROP_SQL = "UPDATE crop_trial SET crop_name = ?, " \
                  "sowing_date = ?, harvest_date = ?, variety = ?, inter_ro_cm = ?, update_date = ? WHERE id = ?;"
DELETE_CROP_SQL = "DELETE FROM crop_trial WHERE id = '{}';"

INSERT_FARMER_SQL = "INSERT INTO farmer (first_name, last_name, address, zipcode, town, country," \
                    "create_date) VALUES (?, ?, ?, ?, ?, ?, ?);"
UPDATE_FARMER_SQL = "UPDATE farmer SET first_name = ?, " \
                    "last_name = ?, address = ?, zipcode = ?, town = ?, country = ?, update_date = ? WHERE id = ?;"
DELETE_FARMER_SQL = "DELETE FROM farmer WHERE id = '{}';"

FETCH_ALL_TRIAL = """SELECT * FROM geostatistic_trial"""
FETCH_ONE_TRIAL = "SELECT * FROM geostatistic_trial WHERE id = '{}';"
FETCH_TRIAL_TEAM = "SELECT * FROM geostatistic_trial WHERE lpc_team_id = '{}';"
FETCH_TRIAL_FARMER = "SELECT * FROM geostatistic_trial WHERE farmer_id = '{}';"
FETCH_TRIAL_CROP = "SELECT * FROM geostatistic_trial WHERE crop_trial_id = '{}';"
INSERT_TRIAL_SQL = "INSERT INTO geostatistic_trial (field_name, field_area, field_irrigation, " \
                   "field_soil, lpc_team_id, farmer_id, crop_trial_id, id_contour, create_date) VALUES (?, ?, ?, ?, ?, " \
                   "?, ?, ?, ?);"
UPDATE_TRIAL_SQL = "UPDATE geostatistic_trial SET field_name = ?, field_area = ?, field_irrigation = " \
                   "?, field_soil = ?, lpc_team_id = ?, farmer_id = ?, crop_trial_id = ?, id_contour = ?, " \
                   "update_date = ? WHERE id = ?;"
DELETE_TRIAL_SQL = "DELETE FROM geostatistic_trial WHERE id = '{}';"

FETCH_ALL_TEAM = "SELECT id, first_name, last_name, create_date, update_date FROM lpc_team;"
FETCH_ONE_TEAM = "SELECT id, first_name, last_name, create_date, update_date FROM lpc_team WHERE id = '{}';"
INSERT_TEAM_SQL = "INSERT INTO lpc_team (first_name, last_name, create_date) VALUES (?, ?, ?);"
UPDATE_TEAM_SQL = "UPDATE lpc_team SET first_name = ?, last_name = ?,  update_date = ? WHERE id = ?;"
DELETE_TEAM_SQL = "DELETE FROM lpc_team WHERE id = '{}';"

VALIDATION_FIELDS = ['estimated', 'error', 'sqr_error', 'rmse', '%_rmse']

# COMPOSER LAYOUT CONSTANTS
from qgis.core import QgsLayoutItem

REFERENCE_POINTS = {
    0: QgsLayoutItem.UpperLeft,
    1: QgsLayoutItem.UpperMiddle,
    2: QgsLayoutItem.UpperRight,
    3: QgsLayoutItem.MiddleLeft,
    4: QgsLayoutItem.Middle,
    5: QgsLayoutItem.MiddleRight,
    6: QgsLayoutItem.LowerLeft,
    7: QgsLayoutItem.LowerMiddle,
    8: QgsLayoutItem.LowerRight
}

COMPOSER_LAYERS = (
    'T1_T2_total', 'T1_total', 'T2_total', 'T1_80_perc', 'T2_80_perc', '1_Krig_T1_T2_total_', '1_Krig_T1_total_',
    '1_Krig_T2_total_', '1_Krig_T1_80_perc_', '1_Krig_T2_80_perc_', 'Yield_Gain')

COMPOSER_LAYOUTS = {
    'T1_T2_total': '01_Points_with_measured_yield_values.qpt',
    'T1_total': '02_T1_Measured_yield.qpt',
    'T2_total': '03_T2_Measured_yield.qpt',
    'T1_80_perc': '04_T1_Sample_for_model_generation.qpt',
    'T2_80_perc': '05_T2_Sample_for_model_generation.qpt',
    '1_Krig_T1_T2_total_': '06_Model_T1_T2.qpt',
    '1_Krig_T1_total_': '07_Model_T1.qpt',
    '1_Krig_T2_total_': '08_Model_T2.qpt',
    '1_Krig_T1_80_perc_': '09_Model_T1_80perc.qpt',
    '1_Krig_T2_80_perc_': '10_Model_T2_80perc.qpt',
    'Yield_Gain': '11_Yield_gain_using_T2.qpt'

}
