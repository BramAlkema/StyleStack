"""Command-line interface for OOXML Round-Trip Testing Utility."""

import click
from pathlib import Path
from typing import List, Optional, Tuple

from .core.config import Config
from .core.logging import setup_logging, get_logger


def version_callback(ctx, param, value):
    """Callback for version option."""
    if not value or ctx.resilient_parsing:
        return
    from . import __version__
    click.echo(f"OOXML Round-Trip Tester version {__version__}")
    ctx.exit()


@click.group()
@click.option("--config", type=click.Path(), help="Configuration file path")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--version", is_flag=True, help="Show version information", expose_value=False, is_eager=True, callback=version_callback)
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: bool, version: bool = False):
    """OOXML Round-Trip Testing Utility.
    
    A comprehensive testing framework for validating OOXML document compatibility
    across different Office platforms through round-trip conversion analysis.
    """
    # Initialize context
    ctx.ensure_object(dict)
    
    # Setup logging
    setup_logging(verbose=verbose)
    logger = get_logger(__name__)
    
    # Load configuration
    try:
        if config and not Path(config).exists():
            click.echo(f"Error: Configuration file not found: {config}", err=True)
            ctx.exit(1)
            
        ctx.obj['config'] = Config.load(config) if config else Config()
        ctx.obj['verbose'] = verbose
        logger.info("CLI initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize CLI: {e}")
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)


@cli.command()
@click.option("--output", "-o", type=click.Path(), required=True,
              help="Output directory for probe files")
@click.option("--format", "output_format", 
              type=click.Choice(['docx', 'pptx', 'xlsx', 'all']),
              default='all', help="Output format for probe files")
@click.option("--features", type=str, 
              help="Comma-separated list of features to test (themes,styles,tables,shapes)")
@click.option("--count", type=int, default=10,
              help="Number of probe files to generate")
@click.pass_context
def probe(ctx: click.Context, output: str, output_format: str, features: Optional[str], count: int):
    """Generate OOXML probe files for testing.
    
    Creates test documents with specific OOXML features to validate
    cross-platform compatibility through round-trip conversion.
    """
    logger = get_logger(__name__)
    config = ctx.obj['config']
    
    try:
        from .probe.generator import ProbeGenerator
        
        # Parse features
        feature_list = []
        if features:
            feature_list = [f.strip() for f in features.split(',')]
        
        # Initialize probe generator
        generator = ProbeGenerator(config)
        
        # Generate probe files
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = generator.generate(
            output_dir=output_path,
            format=output_format,
            features=feature_list,
            count=count
        )
        
        click.echo(f"Generated {len(results)} probe files in {output_path}")
        for result in results:
            click.echo(f"  - {result}")
            
    except Exception as e:
        logger.error(f"Probe generation failed: {e}")
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)


@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--platforms", type=str, 
              help="Comma-separated list of platforms (office,libreoffice,google)")
@click.option("--output", "-o", type=click.Path(),
              help="Output directory for conversion results")
@click.option("--parallel", is_flag=True,
              help="Run conversions in parallel")
@click.option("--tolerance", type=click.Choice(['strict', 'normal', 'lenient', 'permissive']),
              default='normal', help="Tolerance level for pass/fail determination")
@click.option("--fail-threshold", type=float, default=70.0,
              help="Minimum survival rate threshold for CI/CD success (default: 70.0)")
@click.option("--critical-threshold", type=float, default=90.0,
              help="Minimum critical carrier success rate (default: 90.0)")
@click.option("--exit-on-failure", is_flag=True,
              help="Exit with non-zero code if thresholds are not met")
@click.option("--report-format", type=click.Choice(['json', 'csv', 'html', 'all']),
              default='json', help="Report output format")
@click.option("--include-raw-data", is_flag=True,
              help="Include raw analysis data in reports")
@click.pass_context
def test(ctx: click.Context, files: Tuple[str, ...], platforms: Optional[str], 
         output: Optional[str], parallel: bool, tolerance: str, fail_threshold: float,
         critical_threshold: float, exit_on_failure: bool, report_format: str,
         include_raw_data: bool):
    """Run round-trip tests on OOXML files with CI/CD integration.
    
    Converts documents through specified platforms and analyzes differences
    to identify compatibility issues. Supports configurable pass/fail thresholds
    for continuous integration workflows.
    """
    logger = get_logger(__name__)
    config = ctx.obj['config']
    
    try:
        from .convert.engine import ConversionEngine
        from .analyze.xml_parser import OOXMLParser
        from .analyze.carrier_analyzer import StyleStackCarrierAnalyzer
        from .analyze.tolerance_config import ToleranceConfiguration
        from .report.compatibility_matrix import CompatibilityMatrix
        from .report.output_formats import JSONReporter, CSVReporter, HTMLReporter
        from datetime import datetime
        
        # Validate thresholds
        if not (0 <= fail_threshold <= 100):
            click.echo(f"Error: Invalid fail threshold: {fail_threshold}. Must be 0-100.", err=True)
            ctx.exit(1)
        
        if not (0 <= critical_threshold <= 100):
            click.echo(f"Error: Invalid critical threshold: {critical_threshold}. Must be 0-100.", err=True)
            ctx.exit(1)
        
        # Parse platforms
        platform_list = ['microsoft_office', 'libreoffice']  # Default platforms
        if platforms:
            platform_list = [p.strip() for p in platforms.split(',')]
        
        # Setup output directory
        output_path = Path(output) if output else Path.cwd() / "test_results"
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        engine = ConversionEngine()
        xml_parser = OOXMLParser()
        carrier_analyzer = StyleStackCarrierAnalyzer()
        tolerance_config = ToleranceConfiguration()
        tolerance_profile = tolerance_config.get_profile(tolerance)
        matrix_generator = CompatibilityMatrix()
        
        all_analysis_results = []
        overall_results = []
        
        # Process each file
        for file_path in files:
            click.echo(f"Testing {file_path}...")
            
            # Run conversions for each platform
            conversion_results = {}
            for platform in platform_list:
                try:
                    click.echo(f"  Converting on {platform}...")
                    result = engine.run_round_trip(Path(file_path), platform)
                    conversion_results[platform] = result
                    click.echo(f"  ✓ {platform} conversion completed")
                except Exception as e:
                    logger.error(f"  ✗ {platform} conversion failed: {e}")
                    conversion_results[platform] = {'error': str(e)}
            
            # Analyze results for this file
            file_analysis_results = []
            for platform, conv_result in conversion_results.items():
                if 'error' in conv_result:
                    continue
                    
                try:
                    # Analyze XML differences
                    original_doc = xml_parser.parse_document(Path(file_path))
                    converted_doc = xml_parser.parse_document(conv_result['converted_path'])
                    xml_diff = xml_parser.compare_parsed_documents(original_doc, converted_doc)
                    
                    # Map to StyleStack carriers
                    carrier_analysis = carrier_analyzer.analyze_changes(
                        xml_diff, tolerance_config
                    )
                    
                    analysis_result = {
                        'platform': platform,
                        'document_format': _detect_format(Path(file_path)),
                        'xml_changes': xml_diff,
                        'carrier_analysis': carrier_analysis,
                        'conversion_metadata': conv_result.get('metadata', {})
                    }
                    
                    file_analysis_results.append(analysis_result)
                    all_analysis_results.append(analysis_result)
                    
                    click.echo(f"  ✓ {platform} analysis completed")
                except Exception as e:
                    logger.error(f"  ✗ {platform} analysis failed: {e}")
            
            # Generate compatibility matrix for this file
            if file_analysis_results:
                report = matrix_generator.generate_matrix(
                    file_analysis_results,
                    report_config={
                        'tolerance_level': tolerance,
                        'platforms': platform_list,
                        'template_path': str(file_path),
                        'test_timestamp': datetime.now().isoformat()
                    }
                )
                overall_results.append((Path(file_path), report))
        
        # Generate consolidated report if multiple files
        if len(overall_results) > 1:
            click.echo("Generating consolidated compatibility report...")
            consolidated_report = matrix_generator.generate_matrix(
                all_analysis_results,
                report_config={
                    'tolerance_level': tolerance,
                    'platforms': platform_list,
                    'test_type': 'consolidated',
                    'test_timestamp': datetime.now().isoformat()
                }
            )
        else:
            consolidated_report = overall_results[0][1] if overall_results else None
        
        if not consolidated_report:
            click.echo("Error: No successful test results to report", err=True)
            ctx.exit(1)
        
        # Evaluate thresholds
        overall_rate = consolidated_report.overall_metrics.get('overall_survival_rate', 0)
        critical_rate = consolidated_report.overall_metrics.get('critical_carrier_success', 0)
        
        meets_overall = overall_rate >= fail_threshold
        meets_critical = critical_rate >= critical_threshold
        overall_pass = meets_overall and meets_critical
        
        # Save reports
        base_filename = f"stylestack_compatibility_{consolidated_report.report_id}"
        saved_files = []
        
        formats = [report_format] if report_format != 'all' else ['json', 'csv', 'html']
        
        for fmt in formats:
            try:
                if fmt == 'json':
                    reporter = JSONReporter(include_metadata=True)
                    if include_raw_data:
                        content = reporter.create_api_response(consolidated_report, include_raw_data=True)
                        content = __import__('json').dumps(content, indent=2)
                    else:
                        content = reporter.format_report(consolidated_report)
                    filepath = output_path / f"{base_filename}.json"
                    
                elif fmt == 'csv':
                    reporter = CSVReporter(include_headers=True)
                    content = reporter.format_report(consolidated_report)
                    filepath = output_path / f"{base_filename}.csv"
                    
                elif fmt == 'html':
                    reporter = HTMLReporter(include_charts=False)
                    content = reporter.format_report(consolidated_report)
                    filepath = output_path / f"{base_filename}.html"
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                saved_files.append(str(filepath))
                click.echo(f"✓ {fmt.upper()} report saved: {filepath}")
                
            except Exception as e:
                logger.error(f"✗ Failed to save {fmt.upper()} report: {e}")
        
        # Display summary
        click.echo("\n" + "=" * 60)
        click.echo("TEST SUMMARY")
        click.echo("=" * 60)
        click.echo(f"Files Tested: {len(files)}")
        click.echo(f"Platforms: {', '.join(platform_list)}")
        click.echo(f"Overall Survival Rate: {overall_rate:.1f}%")
        click.echo(f"Critical Carrier Success: {critical_rate:.1f}%")
        click.echo(f"Report Files: {', '.join(saved_files)}")
        click.echo("")
        
        if overall_pass:
            click.echo("✓ ALL THRESHOLDS MET - TEST PASSED", color='green')
            return
        else:
            failure_reasons = []
            if not meets_overall:
                failure_reasons.append(f"Overall survival rate {overall_rate:.1f}% below threshold {fail_threshold:.1f}%")
            if not meets_critical:
                failure_reasons.append(f"Critical carrier success {critical_rate:.1f}% below threshold {critical_threshold:.1f}%")
            
            click.echo("✗ THRESHOLD FAILURES:", color='red')
            for reason in failure_reasons:
                click.echo(f"  - {reason}", color='red')
            
            if exit_on_failure:
                click.echo("Exiting with failure code due to --exit-on-failure", color='red')
                ctx.exit(1)
            else:
                click.echo("Continuing despite failures (use --exit-on-failure to exit)")
                return
        
    except SystemExit:
        # Let SystemExit propagate (for ctx.exit calls)
        raise
    except Exception as e:
        logger.error(f"Round-trip testing failed: {e}")
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)


def _detect_format(file_path: Path) -> str:
    """Detect document format from file extension."""
    ext = file_path.suffix.lower()
    if ext in ['.pptx', '.potx']:
        return 'powerpoint'
    elif ext in ['.docx', '.dotx']:
        return 'word'
    elif ext in ['.xlsx', '.xltx']:
        return 'excel'
    else:
        return 'unknown'


@cli.command()
@click.option("--input", "-i", type=click.Path(exists=True),
              help="Input directory with test results")
@click.option("--output", "-o", type=click.Path(), 
              help="Output file for report")
@click.option("--format", "output_format",
              type=click.Choice(['json', 'csv', 'html', 'pdf']),
              default='html', help="Report format")
@click.option("--template", type=str,
              help="Report template name")
@click.pass_context
def report(ctx: click.Context, input: Optional[str], output: Optional[str], 
           output_format: str, template: Optional[str]):
    """Generate compatibility reports.
    
    Creates comprehensive reports from round-trip test results showing
    platform compatibility matrices and identified issues.
    """
    logger = get_logger(__name__)
    config = ctx.obj['config']
    
    try:
        from .report.generator import ReportGenerator
        
        # Setup paths
        input_path = Path(input) if input else Path.cwd() / "test_results"
        output_path = Path(output) if output else Path.cwd() / f"compatibility_report.{output_format}"
        
        # Initialize report generator
        generator = ReportGenerator(config)
        
        # Generate report
        report_file = generator.generate(
            input_dir=input_path,
            output_file=output_path,
            format=output_format,
            template=template
        )
        
        click.echo(f"Report generated: {report_file}")
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)


if __name__ == "__main__":
    cli()