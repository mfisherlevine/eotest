#!/usr/bin/env python
import lsst.eotest.sensor as sensorTest

parser = sensorTest.TaskParser('PSF and system gain characterization from Fe55 data')
parser.add_argument('-f', '--file_pattern', type=str,
                    help='file pattern for Fe55 input files')
parser.add_argument('-F', '--Fe55_file_list', type=str,
                    help='file name of list of Fe55 files')
parser.add_argument('-c', '--chiprob_min', type=float, default=0.1,
                    help='Mininum chi-square probability for cluster fit')
args = parser.parse_args()

task = sensorTest.Fe55Task()

task.config.chiprob_min = args.chiprob_min
task.config.output_dir = args.output_dir
task.config.verbose = args.verbose

infiles = args.files(args.file_pattern, args.Fe55_file_list)

task.run(args.sensor_id, infiles, args.mask_files())