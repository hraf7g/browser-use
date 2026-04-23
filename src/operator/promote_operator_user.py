from __future__ import annotations

import os

from sqlalchemy import select

from src.db.models.user import User
from src.db.session import get_session_factory


def run() -> None:
	"""
	Promote an existing user account to operator role.

	Required env:
	    - UTW_OPERATOR_EMAIL: email of the user to promote
	"""
	email = os.environ.get('UTW_OPERATOR_EMAIL', '').strip().lower()
	if not email:
		raise ValueError('UTW_OPERATOR_EMAIL must be set')

	session_factory = get_session_factory()
	with session_factory() as session:
		user = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
		if user is None:
			raise ValueError(f"user '{email}' was not found")

		user.is_operator = True
		session.commit()

	print(f'promote_operator_user_email={email}')
	print('promote_operator_user_result=success')


if __name__ == '__main__':
	run()
