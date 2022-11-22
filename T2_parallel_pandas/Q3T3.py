import pandas as pd
from collections import Counter
from mpi4py import MPI

comm = MPI.COMM_WORLD
size = comm.Get_size()
rank = comm.Get_rank()


dataset = r'/Data/flight.csv'

if rank == 0:
    def dist_rows(n_rows: int, n_processes):
        reading_info = []
        skip_rows = 1
        reading_info.append([n_rows - skip_rows, skip_rows])
        skip_rows = n_rows
        for _ in range(1, n_processes - 1):
            reading_info.append([n_rows, skip_rows])
            skip_rows = skip_rows + n_rows
        reading_info.append([None, skip_rows])
        return reading_info
    sw = size - 1
    rows = 0
    with open(dataset) as f:
        rows = sum(1 for line in f)
    dist = dist_rows(n_rows=(rows // sw) + 1, n_processes=sw)
    s_time = MPI.Wtime()  
    for worker in range(1, size):
        chunk_to_process = worker - 1
        comm.send(dist[chunk_to_process], dest=worker)
    avg_time = 0
    for worker in (range(1, size)):  # receive
        result = comm.recv(source=worker)
        avg_time += result
    result = f'{(avg_time / sw):.1f}'
    print(f'Average Airtime : {result} minutes')
    total_time = f'{(MPI.Wtime() - s_time):.1f}'
    print(f'Time Taken : {total_time} seconds \n')

elif rank > 0:
    chunk_to_process = comm.recv()
    df = pd.read_csv(dataset, nrows=chunk_to_process[0], skiprows=chunk_to_process[1], names=list(pd.read_csv(dataset, skiprows=0, nrows=0).columns))
    df['FlightDate'] = pd.to_datetime(df['FlightDate'], format='%Y-%m-%d')
    flightss = df[(df.OriginCityName == "Nashville, TN") & (df.DestCityName == "Chicago, IL")]
    comm.send(flightss["AirTime"].mean(), dest=0)