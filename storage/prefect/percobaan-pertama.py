from prefect import flow,task

@task(log_prints=True)
def logging_kedua():
    print("pull code from storage")

@task(log_prints=True)
def logging():
    print("berhasil")

@flow(name="coba")
def main():
    logging()
    logging_kedua()

if __name__ == '__main__':
    main()