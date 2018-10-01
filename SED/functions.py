import argparse

def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--time_range",
        help="give a time range", nargs="+",
        type=float, required=False)
    parser.add_argument(
        "--emin",
        help="The minimum energy for the analysis",
        type=float, default=100)
    parser.add_argument(
        "--emax",
        help="The minimum energy for the analysis",
        type=float, default=800000)
    parser.add_argument(
        "--target_src",
        help="The target source for the analysis",
        type=str, default='3FGL_J0509.4+0541')
    parser.add_argument(
        "--retries",
        help="Number of retries if fit does not converge",
        type=int, default=20)
    parser.add_argument(
        "--free_sources",
        help="Define which sources are free for the fit",
        type=str, nargs="+", required=False)
    parser.add_argument(
        "--free_diff",
        help="Free the isotropic and galactic diffuse component",
        action='store_true', default=False)
    parser.add_argument(
        "--use_3FGL",
        help="Decide of whether or not to use 3FGL sources",
        action='store_true', default=False)
    parser.add_argument(
        "--free_norm",
        help="Only free the normalization of the target",
        action='store_true', default=False)
    parser.add_argument(
        "--no_sed",
        help="Only run llh and bowtie, no sed points",
        action='store_true', default=False)
    parser.add_argument(
        "--src_gamma",
        help="choose a fixed gamma for the target source",
        type=float, required=False)
    parser.add_argument(
        "--free_radius",
        help="free sources in a radius of the target source",
        type=float, required=False)
    parser.add_argument(
        "--data_path",
        help="Path to the data files",
        type=str, required=True)
    parser.add_argument(
        "--xml_path",
        help="path to xml files with additional sources for the model",
        type=str, required=False)
    parser.add_argument(
         "--outfolder",
         help="where to save the output files?",
         type=str, required=False)
    return parser.parse_args().__dict__