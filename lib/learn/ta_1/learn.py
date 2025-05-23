import catboost
import numpy
from lib import docker
from lib.learn.ta_1 import prepare_data
from lib.utils import get_file_abspath_recursive


def learn():
    model = catboost.CatBoostRegressor(
        task_type='CPU',
        verbose=100
    )

    data = prepare_data.get_saved_prepared_data()

    train_pool = catboost.Pool(
        data=catboost.FeaturesData(
            num_feature_data=numpy.array(data['train_x'])
        ),
        label=numpy.array(data['train_y'])
    )

    validate_pool = catboost.Pool(
        data=catboost.FeaturesData(
            num_feature_data=numpy.array(data['validate_x'])
        ),
        label=numpy.array(data['validate_y'])
    )

    model.fit(
        train_pool,
        eval_set=validate_pool,
        plot=True,
    )

    model.save_model(get_model_file_path())

    for i in range(0, 100):
        prediction = predict(data=data['test_x'][i])
        real = data['test_y'][i]
        print(real, abs(prediction - real))


def predict(data: list):
    model = catboost.CatBoostRegressor()
    model.load_model(get_model_file_path())

    return model.predict(data=data)


def get_model_file_path():
    if docker.is_docker():
        return '/app/learn_models/ta-1.txt'

    return get_file_abspath_recursive('ta-1.txt', 'learn_models')
