from datamodels import UserInfo


class UserMapper:
    def __init__(self, df_chunk_generator) -> None:
        self.__df_chunk_generator = df_chunk_generator

    def __map_single_row(self, row):
        return UserInfo(
            codcf=row.codcf,
            # ragsoc1=row.ragsoc1,
            # ragsoc2=row.ragsoc2,
            # tipocf=row.tipocf,
            # giuridica=row.giuridica,
            # natonazcf=row.natonazcf,
            # natocf=row.natocf,
            # datanasc=row.datanasc,
            # indir1=row.indir1,
            # indir2=row.indir2,
            # capcf=row.capcf,
            # citcf=row.citcf,
            # prcf=row.prcf,
            # nazcf=row.nazcf,
            # cfcfsn=row.cfcfsn,
            # cfcf=row.cfcf, 
            # picfsn=row.picfsn,
            # picf=row.picf,
            # sociosn=row.sociosn,
            # numsocio=row.numsocio,
            # pilotasn=row.pilotasn,
            # istrusn=row.istrusn,
            studentsn=row.studentsn,
            email=row.email,
            telefono1=row.telefono1,
            telefono2=row.telefono2
            # note1=row.note1,
            # note2=row.note2,
            # fisosn=row.fisosn,
            # aprsn=row.aprsn,
            # prospectsn=row.prospectsn,
            # obbligatosn=row.obbligatosn,
            # examsn=row.examsn,
            # aec_itasn=row.aec_itasn,
            # prospect_cate=row.prospect_cate,
            # web_password=row.web_password,
            # flag_atoweb=row.flag_atoweb,
            # flag_webunit=row.flag_webunit,
            # flag_reservation=row.flag_reservation,
            # flag_operator=row.flag_operator,
            # flag_master=row.flag_master,
            # flag_cbta=row.flag_cbta,
        )


    def generate_users(self) -> iter:
        # for df_chunk in self.__df_chunk_generator:
        #     for row in df_chunk.itertuples():
        #         yield self.__map_single_row(row)

        user_objects = self.__df_chunk_generator.apply(self.__map_single_row, axis=1)
        yield from user_objects
