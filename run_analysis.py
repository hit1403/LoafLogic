# run_analysis.py
import pandas as pd
import sys
import os
from pathlib import Path
from src.data_analyser import DataAnalyser
from src.data_manager import DataManager

def main():
    print("Starting Bread Price Analysis...")
    print("=" * 50)
    
    # Find the latest data file
    data_manager = DataManager()
    processed_dir = Path("data/processed")
    csv_files = list(processed_dir.glob("bread_prices_analysis_*.csv"))
    
    if not csv_files:
        print("No data files found. Please run the scraper first.")
        return
    
    latest_file = max(csv_files, key=lambda x: x.stat().st_mtime)
    print(f"Using data file: {latest_file.name}")
    
    # Run analysis
    analyser = DataAnalyser()
    
    print("Loading and preprocessing data...")
    df = analyser.load_and_preprocess(latest_file)
    
    # df.to_csv("./after_load_and_preprocess.csv")
    
    print("Matching products across platforms...")
    df_matched = analyser.fuzzy_match_products(df)
    
    # df_matched.to_csv("./after_fuzzy_match_products.csv")
    
    print("Identifying best deals...")
    deals_df = analyser.identify_best_deals(df_matched)
    
    # deals_df.to_csv("./after_identify_best_deals.csv")
    
    print("Generating insights...")
    insights = analyser.generate_insights(deals_df)
    
    print("Creating comparison table...")
    comparison_table = analyser.create_comparison_table(deals_df)
    
    # Save analysis results
    output_file = processed_dir / f"price_comparison_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        comparison_table.to_excel(writer, sheet_name='Product Comparison', index=False)
        deals_df.to_excel(writer, sheet_name='All Deals Analysis', index=False)
        df.to_excel(writer, sheet_name='Raw Data', index=False)
    
    print("=" * 50)
    print("ANALYSIS COMPLETE!")
    print("=" * 50)
    
    # Print key insights
    print("\n KEY INSIGHTS:")
    print(f"• Platforms analyzed: {', '.join(df['platform'].unique())}")
    print(f"• Total products compared: {len(comparison_table)}")
    print(f"• Best deals found: {deals_df['is_best_deal'].sum()}")
    
    platform_best = insights['best_deals_count']
    print(f"• Platform with most best deals: {platform_best.idxmax()} ({platform_best.max()})")
    
    print(f"• Average price difference: {insights['avg_price_difference']:.1f}%")
    print(f"• Maximum savings opportunity: ₹{insights['max_savings_opportunity']:.2f}/100g")
    
    print(f"\nResults saved to: {output_file}")
    print("\nStarting dashboard...")
    
    # Launch dashboard
    os.system("streamlit run dashboard/app.py")

if __name__ == "__main__":
    main()