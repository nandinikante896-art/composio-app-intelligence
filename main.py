import asyncio
import argparse
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
except ImportError as exc:
    if exc.name != "dotenv":
        raise
    def load_dotenv():
        env_file=Path(__file__).resolve().parent/".env"
        if not env_file.exists():
            return
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name,value=line.split("=",1)
            value=value.strip().strip("\"'")
            os.environ.setdefault(name.strip(),value)

load_dotenv()

from src.pipeline.prepare_data import prepare
from src.pipeline.orchestrator import run_pipeline
from src.analysis.dashboard import generate_dashboard
from src.analysis.data_quality import generate_quality_artifacts
from src.tools.llm import check_ollama, configured_model_provider
from src.pipeline.orchestrator import OUTPUT
from src.tools.composio_tools import composio_status

def main():
    parser=argparse.ArgumentParser(description="Composio App Intelligence Agent")
    parser.add_argument("--limit",type=int,default=100)
    parser.add_argument("--workers",type=int,default=3)
    parser.add_argument("--output-dir",type=Path)
    parser.add_argument("--resume",action="store_true")
    parser.add_argument("--prepare-data",action="store_true")
    parser.add_argument("--generate-report",action="store_true")
    parser.add_argument("--audit-quality",action="store_true")
    parser.add_argument("--check-composio",action="store_true")
    args=parser.parse_args()
    if args.prepare_data:
        print(prepare())
        return
    if args.limit<1 or args.limit>100:
        parser.error("--limit must be between 1 and 100")
    if args.workers<1 or args.workers>3:
        parser.error("--workers must be between 1 and 3")
    if args.generate_report:
        print(generate_dashboard())
        return
    if args.audit_quality:
        report=generate_quality_artifacts()
        print(f"Audited {report['dataset_integrity']['json_record_count']} result records.")
        print(f"Generated {report['files_audited']['json']} audit report and {report['manual_verification']['sample_csv']}.")
        return
    if args.check_composio:
        print(composio_status(execute=True))
        return
    try:
        check_ollama()
    except RuntimeError as exc:
        parser.error(f"Research not started; {exc} Existing research files were not changed.")
    output_dir=args.output_dir
    if output_dir is None and args.limit<100:
        stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_dir=OUTPUT/"pilots"/f"limit-{args.limit}-{stamp}"
    try:
        records,metrics,insights=asyncio.run(run_pipeline(
            args.limit,args.workers,output_dir=output_dir,resume=args.resume
        ))
    except RuntimeError as exc:
        print(str(exc),file=sys.stderr)
        raise SystemExit(2) from exc
    print(f"Processed {len(records)} records")
    print(f"Output directory: {output_dir or OUTPUT}")
    print(f"Research provider: {configured_model_provider()} ({os.getenv('OLLAMA_MODEL', 'qwen2.5:3b')})")
    print(f"Human audit completed: {metrics['human_review_completed']}")
    print("No live accuracy can be reported until output/verification_sample.csv is completed.")
    if args.limit==100 and (output_dir is None or output_dir.resolve()==OUTPUT.resolve()):
        report=generate_quality_artifacts()
        print(f"Updated {report['files_audited']['json']} audit report.")

if __name__=="__main__":
    main()
