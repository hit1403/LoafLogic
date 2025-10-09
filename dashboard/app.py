import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Adding src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_analyser import DataAnalyser

st.set_page_config(
    page_title="Bread Price Comparison",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #379836;
        text-align: center;
        margin-bottom: 2rem;
    }
    .best-deal {
        background-color: #D4EDDA;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #32cd2a;
    }
    .metric-card {
        background-color: #379836;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid #2E86AB;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.markdown('<h1 class="main-header"> Bread Price Comparison Dashboard</h1>', 
                unsafe_allow_html=True)
    
    # File upload
    st.sidebar.header("Data Input")
    uploaded_file = st.sidebar.file_uploader("Upload your combined CSV file", type=['csv'],key="file_uploader")
    
    if uploaded_file is not None:
        try:
            # Initializing analyser
            analyser = DataAnalyser()
            
            # Loading and processing data
            with st.spinner("Analyzing bread prices..."):
                df = analyser.load_and_preprocess(uploaded_file)
                df_matched = analyser.fuzzy_match_products(df)
                deals_df = analyser.identify_best_deals(df_matched)
                insights = analyser.generate_insights(deals_df)
                comparison_table = analyser.create_comparison_table(deals_df)
            
            # Display overview metrics
            st.header(" Quick Overview")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_products = len(df)
                st.metric("Total Products", total_products)
            
            with col2:
                platforms = df['platform'].nunique()
                st.metric("Platforms Compared", platforms)
            
            with col3:
                best_deals_count = deals_df['is_best_deal'].sum()
                st.metric("Best Deals Found", best_deals_count)
            
            with col4:
                avg_savings = f"₹{deals_df['savings_opportunity'].mean():.2f}"
                st.metric("Avg Savings Opportunity", avg_savings)
            
            # Platform Comparison
            st.header(" Platform Comparison")
            
            # Only keeping the Price Distribution tab
            # Price distribution
            fig = px.box(df, x='platform', y='price_per_100g',
                       title='Price Distribution per 100g by Platform',
                       labels={'price_per_100g': 'Price per 100g (₹)', 'platform': 'Platform'})
            st.plotly_chart(fig, use_container_width=True)
            
            # ENHANCED Detailed Product Comparison Section
            st.header("Detailed Product Comparison")

            # Filter options with UNIQUE KEYS
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_brands = st.multiselect(
                    "Filter by Brand",
                    options=comparison_table['brand'].unique(),
                    default=comparison_table['brand'].unique()[:3],
                    key="brand_filter_main"
                )

            with col2:
                show_comparable_only = st.checkbox("Show only comparable products", 
                                                 value=False,
                                                 key="comparable_filter_main")

            with col3:
                sort_by = st.selectbox(
                    "Sort by",
                    ["Product Name", "Brand", "Platforms Available", "Best Price"],
                    key="sort_filter_main"
                )

            # Apply filters
            filtered_table = comparison_table[comparison_table['brand'].isin(selected_brands)]

            if show_comparable_only:
                filtered_table = filtered_table[filtered_table['is_comparable'] == True]

            # Sort the table
            if sort_by == "Product Name":
                filtered_table = filtered_table.sort_values('product_name')
            elif sort_by == "Brand":
                filtered_table = filtered_table.sort_values('brand')
            elif sort_by == "Platforms Available":
                filtered_table = filtered_table.sort_values('platforms_available', ascending=False)
            elif sort_by == "Best Price":
                # Sort by the lowest available price per 100g
                def get_min_price(row):
                    prices = []
                    for platform in ['blinkit', 'zepto', 'bbnow']:
                        if pd.notna(row[f'{platform}_per_100g']):
                            prices.append(row[f'{platform}_per_100g'])
                    return min(prices) if prices else float('inf')
                
                filtered_table['min_price'] = filtered_table.apply(get_min_price, axis=1)
                filtered_table = filtered_table.sort_values('min_price')
                filtered_table = filtered_table.drop('min_price', axis=1)

            # Display the enhanced table
            st.subheader(f"Showing {len(filtered_table)} products")

            # Create a more informative display
            for idx, product in filtered_table.iterrows():
                with st.expander(f" {product['product_name']} - {product['brand']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    # Platform data with indicators
                    platforms_data = []
                    for platform in ['blinkit', 'zepto', 'bbnow']:
                        price = product[f'{platform}_price']
                        price_per_100g = product[f'{platform}_per_100g']
                        is_best = product[f'{platform}_is_best']
                        
                        if pd.notna(price):
                            platform_info = {
                                'name': platform.upper(),
                                'price': price,
                                'price_per_100g': price_per_100g,
                                'is_best': is_best,
                                'is_available': True
                            }
                            platforms_data.append(platform_info)
                    
                    # Display available platforms
                    for i, platform_info in enumerate(platforms_data):
                        if i == 0:
                            with col1:
                                if platform_info['is_best']:
                                    st.success(f" **{platform_info['name']}**")
                                    st.write(f"Price: ₹{platform_info['price']}")
                                    st.write(f"Per 100g: ₹{platform_info['price_per_100g']:.2f}")
                                else:
                                    st.info(f"**{platform_info['name']}**")
                                    st.write(f"Price: ₹{platform_info['price']}")
                                    st.write(f"Per 100g: ₹{platform_info['price_per_100g']:.2f}")
                        elif i == 1:
                            with col2:
                                if platform_info['is_best']:
                                    st.success(f" **{platform_info['name']}**")
                                    st.write(f"Price: ₹{platform_info['price']}")
                                    st.write(f"Per 100g: ₹{platform_info['price_per_100g']:.2f}")
                                else:
                                    st.info(f"**{platform_info['name']}**")
                                    st.write(f"Price: ₹{platform_info['price']}")
                                    st.write(f"Per 100g: ₹{platform_info['price_per_100g']:.2f}")
                        else:
                            with col3:
                                if platform_info['is_best']:
                                    st.success(f" **{platform_info['name']}**")
                                    st.write(f"Price: ₹{platform_info['price']}")
                                    st.write(f"Per 100g: ₹{platform_info['price_per_100g']:.2f}")
                                else:
                                    st.info(f"**{platform_info['name']}**")
                                    st.write(f"Price: ₹{platform_info['price']}")
                                    st.write(f"Per 100g: ₹{platform_info['price_per_100g']:.2f}")
                    
                    # Show comparability status
                    if product['is_comparable']:
                        st.success(f" Comparable across {product['platforms_available']} platforms")
                    else:
                        st.warning(f" Available on only 1 platform (no comparison possible)")

            # Also show the raw table for data enthusiasts
            if st.checkbox("Show raw data table", key="raw_data_toggle"):
                st.dataframe(
                    filtered_table.style.format({
                        **{col: '₹{:.2f}' for col in filtered_table.columns if 'price' in col and 'is_best' not in col},
                        **{col: '₹{:.2f}' for col in filtered_table.columns if 'per_100g' in col}
                    }).apply(
                        lambda x: ['background-color: #32cd2a' if 'is_best' in x.name and v else '' for v in x],
                        axis=0
                    ).apply(
                        lambda x: ['color: #28A745; font-weight: bold' if 'is_best' in x.name and v else '' for v in x],
                        axis=0
                    ),
                    use_container_width=True,
                    height=400
                )
                
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            st.info("Please make sure you're uploading the correct CSV file format.")
    else:
        # Welcome message
        st.info(" Please upload your combined CSV file to begin analysis")
        
        # Sample data structure
        st.subheader("Expected Data Format:")
        sample_data = pd.DataFrame({
            'name': ['Britannia Milk Bread', 'Modern Whole Wheat'],
            'brand': ['Britannia', 'Modern'],
            'weight': [400, 350],
            'price': [55.0, 42.0],
            'price_per_100g': [13.75, 12.0],
            'platform': ['blinkit', 'zepto']
        })
        st.dataframe(sample_data)

if __name__ == "__main__":
    main()