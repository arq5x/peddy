import sys
import os.path as op
import multiprocessing as mp
import string
from .pedagree import Ped

def run(args):
    check, pedf, vcf, plot, prefix = args
    # only print warnings for het_check
    p = Ped(pedf, warn=False)
    print(check)
    sys.stdout.flush()
    if plot:
        plot = prefix + "." + check + "-check.png"

    df = getattr(p, check)(vcf, plot=plot)
    df.to_csv(prefix + (".%s.csv" % check), sep=",", index=False)
    if df.shape[0] > 50000 and check == "ped_check":
        # remove unknown relationships that aren't in error.
        df = df[((df.pedigree_relatedness != -1) &
                 (~df.parent_error) &
                 (~df.sample_duplication_error))]
    if check == "ped_check":
        # makes the plot nicer
        df.sort(inplace=True, columns=["pedigree_relatedness"])

    return (check, df.to_json(orient='records'))

def main(vcf, pedf, prefix, plot=False):

    tmpl = string.Template(open(op.join(op.dirname(__file__), "tmpl.html")).read())

    ped = Ped(pedf)
    prefix = prefix.rstrip(".-")
    print("")

    p = mp.Pool(4)
    vals = {'pedigree': ped.to_json(), 'title': op.splitext(op.basename(pedf))[0]}
    for check, json in p.imap(run, [(check, pedf, vcf, plot, prefix) for check
                                    in ("het_check", "ped_check", "sex_check")]):
        vals[check] = json
    sys.stdout.flush()
    p.close()
    with open("%s.html" % prefix, "w") as fh:
        fh.write(tmpl.substitute(**vals))


if __name__ == "__main__":
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument("--plot", default=False, action="store_true")
    p.add_argument("--prefix", help="prefix for output files (default is basename of vcf)")
    p.add_argument("vcf", help="bgzipped and tabix'ed VCF")
    p.add_argument("ped", help="pedigree file")
    a = p.parse_args()
    prefix = a.prefix or a.vcf[:-6]
    main(a.vcf, a.ped, prefix, a.plot)
