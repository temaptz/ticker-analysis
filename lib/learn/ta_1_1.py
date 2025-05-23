import catboost
import pandas
import numpy
from sklearn.metrics import mean_squared_error
from lib import utils, docker
from lib.learn.ta_1.learning_card import LearningCard


def get_saved() -> list[LearningCard]:
    result: list[LearningCard] = []

    # for i in learning_db.get_learning():
    #     c = LearningCard()
    #     c.restore_from_json_db(json_data=i[2])
    #
    #     if c.is_ok and len(c.get_x()) == 61:
    #         result.append(c)

    return result


def prepare_csv():
    saved_cards = get_saved()
    records = []

    for c in saved_cards:
        x = c.get_x()
        y = c.get_y()

        records.append({
            'price': x[0],
            'forecast_price': x[1],
            'revenue_ttm': x[2],
            'ebitda_ttm': x[3],
            'market_capitalization': x[4],
            'total_debt_mrq': x[5],
            'eps_ttm': x[6],
            'pe_ratio_ttm': x[7],
            'ev_to_ebitda_mrq': x[8],
            'dividend_payout_ratio_fy': x[9],
            'price_week_0': x[10],
            'price_week_1': x[11],
            'price_week_2': x[12],
            'price_week_3': x[13],
            'price_week_4': x[14],
            'price_week_5': x[15],
            'price_week_6': x[16],
            'price_week_7': x[17],
            'price_week_8': x[18],
            'price_week_9': x[19],
            'price_week_10': x[20],
            'price_week_11': x[21],
            'price_week_12': x[22],
            'price_week_13': x[23],
            'price_week_14': x[24],
            'price_week_15': x[25],
            'price_week_16': x[26],
            'price_week_17': x[27],
            'price_week_18': x[28],
            'price_week_19': x[29],
            'price_week_20': x[30],
            'price_week_21': x[31],
            'price_week_22': x[32],
            'price_week_23': x[33],
            'price_week_24': x[34],
            'price_week_25': x[35],
            'price_week_26': x[36],
            'price_week_27': x[37],
            'price_week_28': x[38],
            'price_week_29': x[39],
            'price_week_30': x[40],
            'price_week_31': x[41],
            'price_week_32': x[42],
            'price_week_33': x[43],
            'price_week_34': x[44],
            'price_week_35': x[45],
            'price_week_36': x[46],
            'price_week_37': x[47],
            'price_week_38': x[48],
            'price_week_39': x[49],
            'price_week_40': x[50],
            'price_week_41': x[51],
            'price_week_42': x[52],
            'price_week_43': x[53],
            'price_week_44': x[54],
            'price_week_45': x[55],
            'price_week_46': x[56],
            'price_week_47': x[57],
            'price_week_48': x[58],
            'price_week_49': x[59],
            'price_week_50': x[60],
            'result': y,
        })

    print('SAVED DATA LEN', len(saved_cards))
    print('RECORDS LEN', len(records))

    df = pandas.DataFrame(records)

    print(df)
    print('FILE CSV', get_data_frame_csv_file_path())

    df.to_csv(get_data_frame_csv_file_path())


def get_model_file_path():
    if docker.is_docker():
        return '/app/learn_models/ta-1_1.txt'

    return utils.get_file_abspath_recursive('ta-1_1.txt', 'learn_models')


def get_data_frame_csv_file_path():
    if docker.is_docker():
        return '/app/ta-1_1.csv'

    return utils.get_file_abspath_recursive('ta-1_1.csv', 'data_frames')


def learn():
    df = pandas.read_csv(get_data_frame_csv_file_path(), index_col=0)
    x = df.drop(columns=['result'])
    y = df['result']

    x_array = x.values
    y_array = y.values
    count_samples = len(x_array)

    random_indexes = numpy.random.permutation(count_samples)

    x_array = x_array[random_indexes]
    y_array = y_array[random_indexes]

    # Рассчитаем точку разделения (split) на 75%, 20%, 5%
    train_end = int(0.75 * count_samples)  # после train_end заканчивается обучающая часть
    val_end = int(0.95 * count_samples)  # после val_end заканчивается валидационная часть
    # (оставшиеся 5% идут на тест)

    x_train, x_val, x_test = numpy.split(x_array, [train_end, val_end])
    y_train, y_val, y_test = numpy.split(y_array, [train_end, val_end])

    print('X_train shape:', x_train.shape)
    print('X_val shape:', x_val.shape)
    print('X_test shape:', x_test.shape)

    print('Y_train shape:', y_train.shape)
    print('Y_val shape:', y_val.shape)
    print('Y_test shape:', y_test.shape)

    train_pool = catboost.Pool(data=x_train, label=y_train)
    validate_pool = catboost.Pool(data=x_val, label=y_val)
    test_pool = catboost.Pool(data=x_test, label=y_test)

    model = catboost.CatBoostRegressor(
        task_type='CPU',
        iterations=5000,
        learning_rate=0.03,
        random_seed=42,
        verbose=100
    )

    model.fit(
        train_pool,
        eval_set=validate_pool,
        plot=True,
    )

    model.save_model(get_model_file_path())

    y_pred_test = model.predict(test_pool)
    mse_test = mean_squared_error(y_test, y_pred_test)
    print('Test MSE:', mse_test)


def predict(data: list):
    model = catboost.CatBoostRegressor()
    model.load_model(get_model_file_path())

    return model.predict(data=data)
