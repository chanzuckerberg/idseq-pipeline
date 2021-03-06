import os
from .common import *

# output location
OUTPUT_PATH_S3 = os.environ.get('OUTPUT_PATH_S3').rstrip('/')

# input reference
INPUT = os.environ.get('INPUT', '/pub/taxonomy/taxdump.tar.gz')


def make_lineages(version):
    # Install ncbitax2lin
    scratch_dir = os.path.join(os.getcwd(), "idseq-pipeline-lineages")
    execute_command("mkdir -p %s" % scratch_dir)
    work_dir = os.path.join(scratch_dir, "ncbitax2lin")
    execute_command(
        "cd %s; rm -rf ncbitax2lin; git clone https://github.com/chanzuckerberg/ncbitax2lin.git"
        % scratch_dir)

    # Get input reference and version number
    _input_fasta_local, version_number = download_ref_local_with_version_any_type(
        INPUT, work_dir, work_dir)
    command = "cd %s; rm -rfv taxdump; mkdir -p taxdump/taxdump; " % work_dir
    command += "tar zxf %s -C ./taxdump/taxdump" % os.path.basename(
        INPUT)  # this structure is needed for ncbitax2lin 'make'
    execute_command(command)

    # Make and upload lineage files
    execute_command("cd %s; make" % work_dir)
    execute_command("aws s3 cp --quiet %s/taxid-lineages.db %s/" %
                    (work_dir, OUTPUT_PATH_S3))
    execute_command("aws s3 cp --quiet %s/taxid-lineages.csv.gz %s/" %
                    (work_dir, OUTPUT_PATH_S3))
    execute_command("aws s3 cp --quiet %s/names.csv.gz %s/" % (work_dir,
                                                               OUTPUT_PATH_S3))

    # Make and upload deuterostome list
    input_filename = "lineages.csv.gz"
    output_filename = "deuterostome_taxids.txt"
    ## print header and lines containing "Deuterostomia":
    command = "cd %s; zcat %s | awk 'NR==1 || /%s/'" % (work_dir,
                                                        input_filename,
                                                        "Deuterostomia")
    ## keep only the column with header tax_id:
    command += " | awk -F',' -vcol=%s '(NR==1){colnum=-1;for(i=1;i<=NF;i++)if($(i)==col)colnum=i;}{print $(colnum)}'" % "tax_id"
    ## remove the header line:
    command += " | tail -n +2 > %s; " % output_filename
    ## upload output file:
    command += "aws s3 cp --quiet %s %s/" % (output_filename, OUTPUT_PATH_S3)
    execute_command(command)

    # upload version:
    upload_version_tracker(INPUT, 'lineage_and_deuterostome', version_number,
                           OUTPUT_PATH_S3, version)
