from datamodels import LoginInfo
import pandas as pd


class LoginInfoMapper:
    def __init__(self, df: pd.DataFrame) -> None:
        self.df = df

    def __map_single_row(self, row):
        return LoginInfo(
            user_mail=row["user_email"],
            user_password=row["user_password"],
            db_host=row["user_host"],
            db_port=row["user_port"],
            db_name=row["user_db_name"],
            flag_master=row["flag_master"],
            codcf=row["codcf"],
        )

    def generate_login_infos(self):
        # login_infos = []

        # for df in self.__df_chunk_generator:
        #     for index, row in df.iterrows():
        #         yield self.__map_single_row(row)

        logininfomaps_objects = self.df.apply(self.__map_single_row, axis=1)
        return logininfomaps_objects


