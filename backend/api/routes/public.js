const express = require('express');
const logger = require('../utils/logger');
const { createAccount, checkEmail } = require('../utils/connector.js');
const router = express.Router();

/**
 * @swagger
 * /public/account:
 *   post:
 *     tags: [Account]
 *     summary: Create a new user account.
 *     description: Registers a new user with the provided account information. All fields are required.
 *     consumes:
 *       - application/json
 *     parameters:
 *       - in: body
 *         name: user
 *         description: The user object to create.
 *         schema:
 *             type: object
 *             required: [email, userType, fullName, phoneNumber]
 *             properties:
 *                email:
 *                  type: string
 *                  description: The email address for the new account.
 *                userType:
 *                  type: string
 *                  description: The type of the user (admin or tenant).
 *                fullName:
 *                  type: string
 *                  description: The full name of the user.
 *                phoneNumber:
 *                  type: string
 *                  description: The phone number of the user.
 *     security:
 *       - bearerAuth: []
 *     responses:
 *       200:
 *         description: The account has been created successfully.
 *       400:
 *         description: Bad request. Possible reasons include missing required fields, or the email already exists.
 *       500:
 *         description: Internal server error. An unexpected error occurred during account creation.
 */

router.post('/account', async (req, res) => {
    const { email, userType, fullName, phoneNumber } = req.body;

    try {

        const emailExists = await checkEmail(email);

        if (emailExists) {
            logger.warn(`Create Account: Email ${email} already exists.`);
            return res.status(400).json({ message: 'Email already exists' });
        }

        logger.info(`Create Account: New account being created with email: ${email}`);
        const result = await createAccount(email, userType, fullName, phoneNumber);

        if (result) {
            logger.info(`Create Account: Account created successfully`);
            res.status(200).json({ message: 'Account created successfully' });

        }
        else {
            logger.warn(`Create Account: Error creating account`);
            res.status(500).json({ error: 'Internal Server Error' });
        }

    } catch (error) {
        logger.error(`Error creating account: ${error.message}`);
        res.status(500).json({ error: 'Internal Server Error' });
    }
});