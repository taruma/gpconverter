import re
import json
import copy
from pathlib import Path
from ttp import ttp
from zipfile import ZipFile

SOLUMMAA_PATH = Path(__file__).parent


def parse_summary_from_file(file_path, template_path=None):

    with open(file_path, "r") as finput:
        data = finput.read()

    if template_path is not None:
        with open(template_path, "r") as ftemplate:
            ttp_template = ftemplate.read()
    else:
        ttp_template = None

    parser_summary = parse_summary_from_data(data, ttp_template)
    return parser_summary


def parse_summary_from_data(data, ttp_template=None):

    if ttp_template is None:
        default_template_path = SOLUMMAA_PATH / "gpt_template.ttp"
        with open(default_template_path, "r") as ftemplate:
            ttp_template = ftemplate.read()

    ttp_result = ttp(data, ttp_template)
    ttp_result.parse()
    return ttp_result.result()[0][0]


def __convert_to_numeric(dictionary):
    for key, value in dictionary.items():
        dictionary[key] = float(value)


def __summary_load_from_parse(parse_summary, load_name, version):

    load_summary = {}

    if version == "v8":
        load = parse_summary[load_name]
    else:
        load = parse_summary[load_name][0]

    # ---- INFO

    load_summary["INFO_LOAD"] = {
        "load_case": load_name.split("LOAD_")[-1],
        "case_name": load["INFO"]["case_name"],
        "load_type": load["INFO"]["load_type"],
    }

    _info_comp_load = {
        "load_vertical": load["INFO_COMPUTATION"]["EQUIVALENT_1"]["load_vert"],
        "load_horizontal_y": load["INFO_COMPUTATION"]["EQUIVALENT_1"]["load_hor_y"],
        "load_horizontal_z": load["INFO_COMPUTATION"]["EQUIVALENT_1"]["load_hor_z"],
        "moment_x": load["INFO_COMPUTATION"]["EQUIVALENT_2"]["mom_x"],
        "moment_y": load["INFO_COMPUTATION"]["EQUIVALENT_2"]["mom_y"],
        "moment_z": load["INFO_COMPUTATION"]["EQUIVALENT_2"]["mom_z"],
    }

    _info_comp_disp = {
        "vertical": load["INFO_COMPUTATION"]["DISPLACEMENT_1"]["disp_vert"],
        "horizontal_y": load["INFO_COMPUTATION"]["DISPLACEMENT_1"]["disp_hor_y"],
        "horizontal_z": load["INFO_COMPUTATION"]["DISPLACEMENT_1"]["disp_hor_z"],
        "angle_rotation_x": load["INFO_COMPUTATION"]["DISPLACEMENT_2"]["rot_x"],
        "angle_rotation_y": load["INFO_COMPUTATION"]["DISPLACEMENT_2"]["rot_y"],
        "angle_rotation_z": load["INFO_COMPUTATION"]["DISPLACEMENT_2"]["rot_z"],
    }

    __convert_to_numeric(_info_comp_load)
    __convert_to_numeric(_info_comp_disp)

    load_summary["INFO_COMPUTATION"] = {
        "LOAD": _info_comp_load,
        "DISPLACEMENT": _info_comp_disp,
    }

    # ---- TABLE
    # |> REDUCTION FACTOR

    load_summary["TABLE"] = {
        "reduction_factor": load["TABLE_REDUCTION_FACTOR"]["DATA"],
    }

    load_summary["INFO_LOAD"]["total_pile"] = len(
        load_summary["TABLE"]["reduction_factor"]
    )

    # |> GLOBAL

    load_summary["TABLE"]["GLOBAL"] = {
        "pile_top_displacements": (
            load["GLOBAL_COORDINATE"]["TABLE_GLOBAL_PILE_TOP_DISPLACEMENTS"]["DATA"]
        ),
        "pile_top_reactions": (
            load["GLOBAL_COORDINATE"]["TABLE_GLOBAL_PILE_TOP_REACTIONS"]["DATA"]
        ),
    }

    # |> LOCAL

    # ==> PILE TOP REACTIONS

    if version == "v8":
        data_local_top_react = load["LOCAL_COORDINATE"][
            "TABLE_LOCAL_PILE_TOP_REACTIONS"
        ]["DATA"]
    else:
        data_local_top_react_1 = load["LOCAL_COORDINATE"][
            "TABLE_LOCAL_PILE_TOP_REACTIONS"
        ]["DATA_1"]
        data_local_top_react_2 = load["LOCAL_COORDINATE"][
            "TABLE_LOCAL_PILE_TOP_REACTIONS"
        ]["DATA_2"]
        data_local_top_react = [
            data_1 | data_2
            for data_1, data_2 in zip(data_local_top_react_1, data_local_top_react_2)
        ]

    load_summary["TABLE"]["LOCAL"] = {
        "pile_top_displacements": (
            load["LOCAL_COORDINATE"]["TABLE_LOCAL_PILE_TOP_DISPLACEMENTS"]["DATA"]
        ),
        "pile_top_reactions": (data_local_top_react),
        "lateral_minimum": (
            load["LOCAL_COORDINATE"]["TABLE_LOCAL_LATERAL_MINIMUM"]["DATA"]
        ),
        "lateral_maximum": (
            load["LOCAL_COORDINATE"]["TABLE_LOCAL_LATERAL_MAXIMUM"]["DATA"]
        ),
    }

    return load_summary


def gpt_summary_from_parse(parse_summary, version):

    gpt_summary = {}

    if "HEADER_VERSION" in parse_summary:
        info_group_version = parse_summary["HEADER_VERSION"]["group_version"]
    else:
        info_group_version = "N/A"

    info_datetime = " ".join(parse_summary["HEADER_DATETIME"].values())
    load_keys = [key for key in parse_summary if "LOAD" in key]

    gpt_summary["INFO"] = {
        "group_version": info_group_version,
        "datetime": info_datetime,
        "computation_name": parse_summary["HEADER_COMPUTATION"]["comp_name"],
        "load_keys": load_keys,
        "total_load_case": len(load_keys),
    }

    # LOAD

    gpt_summary["LOAD"] = {}

    for each_load in load_keys:
        gpt_summary["LOAD"][each_load] = __summary_load_from_parse(
            parse_summary, each_load, version
        )

    gpt_summary["INFO"]["total_pile"] = gpt_summary["LOAD"][each_load]["INFO_LOAD"][
        "total_pile"
    ]

    return gpt_summary


def get_gpt_version(filename):
    filename = Path(filename)

    file_suffix = filename.suffix

    suffix_version = re.search("^.gp(.+)t$", file_suffix).group(1)
    file_version = "v" + suffix_version

    return file_version


def read_gpt_from_file(filename, template_path=None):

    gpt_version = get_gpt_version(filename)

    parse_output = parse_summary_from_file(filename, template_path)
    summary = gpt_summary_from_parse(parse_output, gpt_version)

    return summary


def gpt_summary_to_json(gpt_summary, filename):
    with open(filename, "w") as fj:
        json.dump(gpt_summary, fj)
    return filename


def gpt_summary_from_json(filename):
    with open(filename, "r") as fo:
        gpt_summary = json.load(fo)
    return gpt_summary


def read_gpt_from_zip(zipfilename, ttp_template=None):

    with ZipFile(zipfilename, "r") as zip_ref:
        filename = zip_ref.namelist()[0]
        gpt_version = get_gpt_version(filename)
        with zip_ref.open(filename, "r") as fgpt:
            data = fgpt.read().decode("UTF-8")

    parse_summary = parse_summary_from_data(data, ttp_template)
    gpt_summary = gpt_summary_from_parse(parse_summary, gpt_version)

    return gpt_summary


def __add_prefix_records(records, prefix, ignore_list):

    update_records = copy.deepcopy(records)

    for row in update_records:
        for key in list(row):
            if key not in ignore_list:
                row[prefix + key] = row.pop(key)

    return update_records


def __load_records(gpt_summary, load_case):

    load = gpt_summary["LOAD"][load_case]["TABLE"]
    load_global = load["GLOBAL"]
    load_local = load["LOCAL"]

    rec_rf = load["reduction_factor"]
    rec_global_disp = load_global["pile_top_displacements"]
    rec_global_react = load_global["pile_top_reactions"]
    rec_local_disp = load_local["pile_top_displacements"]
    rec_local_react = load_local["pile_top_reactions"]
    rec_local_lat_min = load_local["lateral_minimum"]
    rec_local_lat_max = load_local["lateral_maximum"]

    rec_global_disp, rec_global_react = map(
        lambda x: __add_prefix_records(x, "global_", ["pile_group"]),
        [rec_global_disp, rec_global_react],
    )

    rec_local_disp, rec_local_react = map(
        lambda x: __add_prefix_records(x, "local_", ["pile_group"]),
        [rec_local_disp, rec_local_react],
    )

    rec_local_lat_min = __add_prefix_records(
        rec_local_lat_min, "local_min_", ["pile_group"]
    )
    rec_local_lat_max = __add_prefix_records(
        rec_local_lat_max, "local_max_", ["pile_group"]
    )

    load_records = []

    zip_gpt = zip(
        rec_rf,
        rec_global_disp,
        rec_global_react,
        rec_local_disp,
        rec_local_react,
        rec_local_lat_min,
        rec_local_lat_max,
    )

    load_case_name = gpt_summary["LOAD"][load_case]["INFO_LOAD"]['load_case']
    case_name = gpt_summary["LOAD"][load_case]["INFO_LOAD"]['case_name']
    load_type = gpt_summary["LOAD"][load_case]["INFO_LOAD"]['load_type']

    for index, item in enumerate(zip_gpt):
        new_item = {}
        new_item["pile_id"] = f"p{index}_{load_case}"
        new_item["load_id"] = load_case
        new_item["load_case"] = load_case_name
        new_item["case_name"] = case_name
        new_item["load_type"] = load_type
        for each_rec in item:
            new_item.update(each_rec)
        load_records.append(new_item)

    return load_records


def gpt_records_from_summary(gpt_summary):

    load_keys = gpt_summary["INFO"]["load_keys"]

    gpt_records = []
    for load_case in load_keys:
        load_records = __load_records(gpt_summary, load_case)
        gpt_records += load_records

    return gpt_records
