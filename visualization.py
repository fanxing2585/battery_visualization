import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO
import base64

data = pd.read_csv("storage_registrations.csv")

# Data processing: Handle null values
data.dropna(subset=['Power_in_kW', 'Energy_in_kWh', 'Installation_Date', 'Battery_Technology'], inplace=True)

df = pd.DataFrame(data)

app = dash.Dash(__name__)


# Get the unique battery technology types from the dataset
available_battery_types = df['Battery_Technology'].unique()

# Create dropdown options from the unique battery types
dropdown_options = [{'label': tech_type, 'value': tech_type} for tech_type in available_battery_types]


# Define the layout of the dashboard
app.layout = html.Div([
    html.H1('Energy Installation Dashboard'),
    
    dcc.Graph(id='scatter-plot'),
    
    dcc.Dropdown(
        id='battery-selector',
        options=dropdown_options,
        value=available_battery_types,  # Set initial selected values (all available types)
        multi=True  # Allow multiple selections
    ),
    
    dcc.Graph(id='box-plot'),
    
    dcc.Graph(id='stacked-bar-chart'),
    
    dcc.Graph(id='battery-technology-pie'),
    
    html.Div(id='correlation-heatmap')
    
])

# Define callback for updating the scatter plot
@app.callback(
    Output('scatter-plot', 'figure'),
    [Input('battery-selector', 'value')]
)
def update_scatter_plot(selected_battery):
    if not isinstance(selected_battery, list):
        selected_battery = [selected_battery]
    filtered_df = df[df['Battery_Technology'].isin(selected_battery)]
    fig = px.scatter(filtered_df, x='Power_in_kW', y='Energy_in_kWh', color='Battery_Technology', title='Power vs. Energy')
    return fig

# Define callback for updating the box plot
@app.callback(
    Output('box-plot', 'figure'),
    [Input('battery-selector', 'value')]
)
def update_box_plot(selected_battery):
    if not isinstance(selected_battery, list):
        selected_battery = [selected_battery]

    filtered_df = df[df['Battery_Technology'].isin(selected_battery)]
    fig = go.Figure()

    for tech_type in selected_battery:
        filtered_tech_df = filtered_df[filtered_df['Battery_Technology'] == tech_type]
        fig.add_trace(go.Box(y=filtered_tech_df['Power_in_kW'], name=tech_type))

    fig.update_layout(title='Box Plot of Power Capacity', yaxis_title='Power_in_kW')
    return fig

# Define callback for updating the stacked bar chart
@app.callback(
    Output('stacked-bar-chart', 'figure'),
    [Input('battery-selector', 'value')]
)
def update_stacked_bar_chart(selected_battery):
    if not isinstance(selected_battery, list):
        selected_battery = [selected_battery]

    filtered_df = df[df['Battery_Technology'].isin(selected_battery)]
    filtered_df['Year'] = pd.to_datetime(filtered_df['Installation_Date']).dt.year  # Extract the year

    fig = go.Figure()

    for tech_type in selected_battery:
        filtered_tech_df = filtered_df[filtered_df['Battery_Technology'] == tech_type]
        tech_counts = filtered_tech_df['Year'].value_counts().sort_index()

        fig.add_trace(go.Bar(x=tech_counts.index, y=tech_counts, name=tech_type))

    fig.update_layout(title='Battery Technology Over Time', xaxis_title='Installation Year', yaxis_title='Count of Installations', barmode='stack')
    return fig

# Define callback for updating the battery technology pie chart
@app.callback(
    Output('battery-technology-pie', 'figure'),
    [Input('battery-selector', 'value')]
)
def update_battery_technology_pie(selected_battery):
    filtered_df = df[df['Battery_Technology'].isin(selected_battery)]

    pie_data = filtered_df['Battery_Technology'].value_counts()

    fig = go.Figure(data=[go.Pie(labels=pie_data.index, values=pie_data.values)])
    fig.update_layout(title='Battery Technology Distribution')
    return fig

# Define callback for updating the correlation heatmap
@app.callback(
    Output('correlation-heatmap', 'children'),
    [Input('battery-selector', 'value')]
)
def update_correlation_heatmap(selected_battery):
    filtered_df = df[df['Battery_Technology'].isin(selected_battery)]

    # Select the relevant columns for correlation
    relevant_columns = ['Power_in_kW', 'Energy_in_kWh', 'Installation_Date', 'Battery_Technology']
    numeric_columns = filtered_df[relevant_columns].select_dtypes(include=['number'])

    # Create a correlation matrix
    correlation_matrix = numeric_columns.corr()

    # Generate the correlation heatmap using seaborn
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title('Correlation Heatmap')

    # Save the heatmap to a temporary file
    plt.savefig('temp.png')
    plt.close()

    # Display the image in the dashboard
    with open('temp.png', 'rb') as img_file:
        encoded_image = base64.b64encode(img_file.read()).decode()

    return html.Img(src='data:image/png;base64,{}'.format(encoded_image))

                     
if __name__ == '__main__':
    app.run_server(debug=True)