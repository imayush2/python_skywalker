import pandas as pd
from sqlalchemy import create_engine

df = pd.read_excel(r"/Users/ayushgupta/Desktop/test/Database\Liver cancer_results_20250312_173902.xlsx")

engine = create_engine('mysql+pymysql://root:8287447641@localhost/scraping_db')


# Insert all rows from the DataFrame into the 'users' table (or your table name)
df.to_sql('users', engine, if_exists='append', index=False)

print("Data inserted successfully.")