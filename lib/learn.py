import catboost
import numpy
import prepare_data


def learn():
    regressor = catboost.CatBoostRegressor(task_type='CPU')

    data = prepare_data.get_saved_prepared_data()

    train_pool = catboost.Pool(
        data=catboost.FeaturesData(
            num_feature_data=numpy.array(data['train_x'])
        ),
        label=numpy.array(data['train_y'])
    )

    regressor.fit(
        train_pool,
        verbose=False,
        plot=True
    )
    return
