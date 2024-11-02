import catboost
import numpy
import prepare_data
import utils

model_file_path = '/Users/artem/PycharmProjects/ticker-analysis/learn.txt'


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

    model.save_model(model_file_path)

    for i in range(0, 100):
        prediction = predict(data=data['test_x'][i])
        real = data['test_y'][i]
        print(real, abs(prediction - real))


def predict(data: list):
    model = catboost.CatBoostRegressor()
    model.load_model(model_file_path)

    return model.predict(data=data)
