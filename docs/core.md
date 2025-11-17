# [core](../features/core/)
## description
a core module for AInsight

## contents
### [models](../features/core/models.py)
#### User
a model for recording user information
#### BaseModel
a abstract model for recording basic information such as created_by_user, created_at, updated_by_user, updated_at, is_deleted, deleted_by_user, etc.

__*every model in another app must inherit this class*__

### [admin](../features/core/admin.py)
#### BaseAdmin
base admin class for other admin register class in another app

__*every admin register class in another app must inherit this class*__
#### UserAdmin
user admin register class

